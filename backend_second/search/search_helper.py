import numpy as np
from pymilvus import Collection, AnnSearchRequest, WeightedRanker, MilvusException
from sentence_transformers import SentenceTransformer, CrossEncoder
from backend_second.utils.config import COLLECTION_NAME_SECOND, MODEL, RERANKER_MODEL
from backend_second.utils.feature.cache import get_cached, store_cache
from backend_second.search.history_score import HistoryScore

class SearchEngine:
    def __init__(self):
        self.model = SentenceTransformer(MODEL)
        self.reranker = CrossEncoder(RERANKER_MODEL)
        self.history_scorer = HistoryScore()
        self.hybrid_weights = [0.7, 0.3]


    def _convert_numpy_types(self, obj):
        """Recursively convert numpy types to native Python types"""
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(x) for x in obj]
        return obj

    def build_milvus_filter(self, parsed_query: dict):
        conditions = []

        if intent := parsed_query.get("intent"):
            conditions.append(f'type == "{intent}"')

        if af := parsed_query.get("amount_filter"):
            op_map = {">": ">", "<": "<", "=": "==", ">=": ">=", "<=": "<=", "!=": "!="}
            if op := op_map.get(af["operator"]):
                conditions.append(f'amount {op} {af["amount"]}')
        elif amount := parsed_query.get("amount"):
            conditions.append(f'amount == {amount}')

        date_condition = None
        if df := parsed_query.get("date_filter"):
            if df["operator"] == "between":
                start = df["start"] + "T00:00:00" if "T" not in df["start"] else df["start"]
                end = df["end"] + "T23:59:59" if "T" not in df["end"] else df["end"]
                date_condition = f'date >= "{start}" and date <= "{end}"'
            elif df["operator"] in {">", "<", ">=", "<=", "==", "!="}:
                date = df["date"] + "T00:00:00" if "T" not in df["date"] else df["date"]
                date_condition = f'date {df["operator"]} "{date}"'
        elif date := parsed_query.get("date"):
            date_condition = f'date like "{date}%"'

        if date_condition:
            conditions.append(date_condition)

        return " and ".join(conditions) if conditions else ""

    def hybrid_search(self, queries: list, top_k: int):
        """Native Milvus hybrid search combining dense and sparse vectors"""
        batch_results = {}
        try:
            collection = Collection(COLLECTION_NAME_SECOND)
            collection.load()
        except Exception as e:
            print(f"Collection load error: {e}")
            return {q["id"]: [] for q in queries}

        for query in queries:
            query_id = query["id"]
            raw_query = query["raw_query"]

            query_dense_emb = self.model.encode([raw_query]).tolist()[0]

            filter_expr = self.build_milvus_filter(query["parsed_query"])
            print(f"Query {query_id} filter expression: '{filter_expr}'")

            try:
                dense_search = AnnSearchRequest(
                    [query_dense_emb],
                    "embedding",
                    {"metric_type": "IP", "params": {"ef": 64}},
                    limit=top_k * 3,
                )
                sparse_search = AnnSearchRequest(
                    [raw_query],
                    "sparse_emb",
                    {"metric_type": "BM25", "params": {}},
                    limit=top_k * 3,
                    expr=filter_expr
                )

                results = collection.hybrid_search(
                    [sparse_search, dense_search],
                    rerank=WeightedRanker(*self.hybrid_weights),
                    limit=top_k,
                    output_fields=["id", "type", "category", "text", "date", "amount", "metadata", "embedding"],
                    timeout=30.0
                )

                batch_results[query_id] = []
                for hits in results:
                    for hit in hits:
                        batch_results[query_id].append({
                            "id": hit.get("id"),
                            "type": hit.get("type"),
                            "category": hit.get("category", ""),
                            "text": hit.get("text", ""),
                            "date": hit.get("date", ""),
                            "amount": hit.get("amount"),
                            "metadata": hit.get("metadata", {}),
                            "embedding": hit.get("embedding"),
                            "score": float(hit.score)
                        })
            except MilvusException as e:
                print(f"Milvus-specific error: {e}")
                batch_results[query_id] = []
            except Exception as e:
                print(f"General error: {e}")
                batch_results[query_id] = []

        return batch_results

    def apply_history_diversity_boost(self, candidates: list):
        recent_embeddings = self.history_scorer.refresh_history(limit=5)
        if not recent_embeddings or not candidates:
            return candidates

        for candidate in candidates:
            cand_emb = candidate.get('embedding')
            if cand_emb is None:
                candidate["history_diversity_score"] = 0.0
                continue

            cand_emb = np.array(cand_emb)
            cand_emb_norm = cand_emb / np.linalg.norm(cand_emb)

            max_sim = 0
            for hist_emb in recent_embeddings:
                hist_emb_norm = hist_emb / np.linalg.norm(hist_emb)
                sim = np.dot(cand_emb_norm, hist_emb_norm)
                if sim > max_sim:
                    max_sim = sim

            diversity_boost = 1.0 - max_sim
            candidate["score"] = candidate["score"] * 0.7 + diversity_boost * 0.3
            candidate["history_diversity_score"] = diversity_boost

        return candidates

    def rerank_results(self, raw_query: str, candidates: list):
        if not candidates:
            return candidates

        texts = [cand.get('text', '') for cand in candidates]
        pairs = [(raw_query, text) for text in texts]

        rerank_scores = self.reranker.predict(pairs)
        for idx, cand in enumerate(candidates):
            cand["rerank_score"] = float(rerank_scores[idx])
            cand["score"] = cand["score"] * 0.4 + cand["rerank_score"] * 0.6

        return candidates

    def process_query_batch(self, batch: list, top_k: int = 5):
        results = {}
        uncached_queries = []

        # Cache check
        for query in batch:
            if cached := get_cached(query["parsed_query"], top_k):
                results[query["id"]] = cached
            else:
                uncached_queries.append(query)

        if not uncached_queries:
            return results

        hybrid_results = self.hybrid_search(uncached_queries, top_k * 3)

        for query in uncached_queries:
            query_id = query["id"]
            parsed_query = query["parsed_query"]
            raw_query = query["raw_query"]

            candidates = hybrid_results.get(query_id, [])

            if candidates:
                # Sort by initial score
                candidates.sort(key=lambda x: x["score"], reverse=True)

                # Apply history-based diversity boosting
                candidates = self.apply_history_diversity_boost(candidates)

                # Rerank results
                candidates = self.rerank_results(raw_query, candidates)

                # Final sort and limit
                candidates.sort(key=lambda x: x["score"], reverse=True)
                final_results = candidates[:top_k]

                for result in final_results:
                    result.pop("embedding", None)
                    print(f"ID: {result['id']}, Final Score: {result['score']:.4f}, "
                          f"Rerank Score: {result.get('rerank_score', 0):.4f}, "
                          f"History Diversity: {result.get('history_diversity_score', 0):.4f}")
            else:
                final_results = []

            results[query_id] = final_results
            store_cache(parsed_query, top_k, final_results)

            print(f"Query {query_id}: Found {len(final_results)} results")

        return results