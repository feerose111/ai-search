from pymilvus import Collection, connections
from sentence_transformers import SentenceTransformer
from backend.utils.config import MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME, MODEL
from backend.utils.feature.cache import get_cached, store_cache
from backend.utils.feature.history import log_query
import time

# Connect to Milvus
connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
collection = Collection(COLLECTION_NAME)
collection.load()

model = SentenceTransformer(MODEL)

from backend.utils.elastic_search.es_client import get_es, INDEX_NAME


def search_documents(query: str, parsed_query: dict, top_k: int = 5):
    # Step 1: Check cache
    log_query(raw_query=query, parsed_query=parsed_query)
    cached = get_cached(parsed_query, top_k)
    if cached:
        return cached

    # Step 2: Semantic search (Milvus)
    t_start = time.time()
    embedding = model.encode(parsed_query["raw_query"]).tolist()
    search_params = {"metric_type": "IP", "params": {"ef": 64}}

    milvus_results = collection.search(
        data=[embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k * 4,
        output_fields=["id", "type", "category", "date", "text", "metadata", "amount"]
    )[0]

    milvus_time = time.time() - t_start
    milvus_ids = [hit.entity.get("id") for hit in milvus_results]
    print(f"[Milvus] Returned: {len(milvus_results)} results in {milvus_time:.2f}s")

    if not milvus_results:
        return []

    milvus_hits = []
    for hit in milvus_results:
        milvus_hits.append({
            "id": hit.entity.get("id"),
            "score": hit.score,
            "entity": hit.entity
        })

    es = get_es()

    def build_must_clauses(parsed_query, milvus_ids, strict=True):
        must = [{"terms": {"id": milvus_ids}}]

        if strict:
            # Lowercase intent
            intent = parsed_query.get("intent")
            if intent:
                must.append({"term": {"type": intent.lower()}})

            # Amount filter fix
            af = parsed_query.get("amount_filter")
            if af:
                op_map = {">": "gt", "<": "lt", "=": "eq"}
                op = op_map.get(af["operator"])
                if op == "eq":
                    must.append({"term": {"amount": af["amount"]}})
                elif op:
                    must.append({"range": {"amount": {op: af["amount"]}}})

            # Date filter with fallback on created_at if date not present
            df = parsed_query.get("date_filter")
            if df:
                date_range = {}
                if df["operator"] == "between":
                    date_range = {"gte": df["start"], "lte": df["end"]}
                elif df["operator"] == ">":
                    date_range = {"gt": df["date"]}
                elif df["operator"] == "<":
                    date_range = {"lt": df["date"]}

                if date_range:
                    must.append({
                        "bool": {
                            "should": [
                                {"range": {"date": date_range}},
                                {"range": {"created_at": date_range}}
                            ]
                        }
                    })

            # Keyword filter (optional enhancement)
            keywords = parsed_query.get("keywords", [])
            if keywords:
                must.append({
                    "bool": {
                        "should": [
                            {"match": {"description": kw}} for kw in keywords
                        ] + [
                            {"match": {"category": kw}} for kw in keywords
                        ]
                    }
                })

        return must

    # Step 4: Elasticsearch strict filtering
    must = build_must_clauses(parsed_query, milvus_ids, strict=True)
    es_query = {"query": {"bool": {"must": must}}}

    t_start = time.time()
    es_resp = es.search(index=INDEX_NAME, body=es_query, size=top_k * 4)
    es_time = time.time() - t_start
    es_hits = es_resp["hits"]["hits"]
    es_hit_map = {hit["_source"]["id"]: hit for hit in es_hits}
    valid_ids = set(es_hit_map.keys())
    print(f"[Elasticsearch] Strict filter matched: {len(valid_ids)} out of {len(milvus_ids)} in {es_time:.2f}s")

    # Step 5: Loose filter fallback
    if not valid_ids:
        must = build_must_clauses(parsed_query, milvus_ids, strict=False)
        es_query = {"query": {"bool": {"must": must}}}
        es_resp = es.search(index=INDEX_NAME, body=es_query, size=top_k * 4)
        es_hits = es_resp["hits"]["hits"]
        es_hit_map = {hit["_source"]["id"]: hit for hit in es_hits}
        valid_ids = set(es_hit_map.keys())
        print(f"[Elasticsearch] Loose filter matched: {len(valid_ids)} out of {len(milvus_ids)}")

    # Debug to find out what got filtered
    milvus_returned_ids = set([hit["id"] for hit in milvus_hits])
    missing_ids = milvus_returned_ids - valid_ids
    print(f"❗ Filtered out IDs by ES: {missing_ids}")

    # Step 6: Combine & sort
    final_candidates = []
    for hit in milvus_hits:
        doc_id = hit["id"]
        if doc_id not in valid_ids:
            continue

        milvus_score = hit["score"]
        es_score = es_hit_map.get(doc_id, {}).get("_score", 0)
        combined_score = 0.7 * milvus_score + 0.3 * es_score

        entity = hit["entity"]
        meta = entity.get("metadata") or {}

        item = {
            "id": entity.get("id"),
            "type": entity.get("type"),
            "category": entity.get("category", ""),
            "title": entity.get("text", ""),
            "date": entity.get("date", ""),
            "combined_score": combined_score
        }

        if item["type"] == "transaction":
            item["amount"] = entity.get("amount")
            item["merchant"] = meta.get("merchant_name")
        elif item["type"] == "product":
            item["price"] = meta.get("price")
            item["vendor"] = meta.get("vendor")
        elif item["type"] == "saved_payment":
            item["amount"] = entity.get("amount")
            item["payee"] = meta.get("payee_name")
        elif item["type"] == "service":
            item["content"] = meta.get("content")

        final_candidates.append(item)

    # === filter function: properly indented inside search_documents ===
    def filter_by_amount_date(item, parsed_query):
        # Check amount filter
        af = parsed_query.get("amount_filter")
        if af and "amount" in item:
            op = af.get("operator")
            target_amount = af.get("amount")
            item_amount = item.get("amount")
            if item_amount is None:
                return False
            if op == "=" and item_amount != target_amount:
                return False
            elif op == ">" and item_amount <= target_amount:
                return False
            elif op == "<" and item_amount >= target_amount:
                return False

        # Check date filter
        df = parsed_query.get("date_filter")
        if df and "date" in item:
            item_date_str = item.get("date")
            if not item_date_str:
                return False
            # Convert string date to datetime for comparison
            from dateutil.parser import parse as parse_date
            item_date = parse_date(item_date_str)

            if df["operator"] == "between":
                start_date = parse_date(df["start"])
                end_date = parse_date(df["end"])
                if item_date < start_date or item_date > end_date:
                    return False
            elif df["operator"] == ">":
                cmp_date = parse_date(df["date"])
                if item_date <= cmp_date:
                    return False
            elif df["operator"] == "<":
                cmp_date = parse_date(df["date"])
                if item_date >= cmp_date:
                    return False

        return True

    # Filter final_candidates by amount and date
    final_candidates = [item for item in final_candidates if filter_by_amount_date(item, parsed_query)]

    # Sort and limit final results
    final_candidates.sort(key=lambda x: x["combined_score"], reverse=True)
    final_results = final_candidates[:top_k]

    print(f"[Final Results] Returned: {len(final_results)} out of {len(milvus_hits)} matched by ES")

    store_cache(parsed_query, top_k, final_results)
    return final_results
