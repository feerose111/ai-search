from fastapi import APIRouter, HTTPException, Query
from backend_second.utils.parser.query_parser import parse_query
from backend_second.utils.feature.logger import setup_logger
import logging
from backend_second.utils.feature.history import get_history, log_query
import uuid
from backend_second.utils.feature.history import history_service
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()
setup_logger()
log_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="log_worker")

search_engine = None

def get_search_engine():
    global search_engine
    if search_engine is None:
        from backend_second.search.search_helper import SearchEngine
        search_engine = SearchEngine()
    return search_engine

@router.get("/search")
def search(q: str, top_k: int = Query(5, ge=1, le=20)):
    try:
        parsed = parse_query(q)
        engine = get_search_engine()

        log_executor.submit(log_query, q, parsed)
        if history_service:
            log_executor.submit(history_service.log_query, q)  # Milvus/Kafka

        batch_id = str(uuid.uuid4())
        query_batch = [{
            "id": batch_id,
            "raw_query": parsed["raw_query"],
            "parsed_query": parsed
        }]
        batch_results = engine.process_query_batch(query_batch, top_k)
        results = batch_results.get(batch_id, [])

        return {"parsed_query": parsed, "results": results}

    except Exception as e:
        logging.exception("Search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/history")
def get_query_history():
    try:
        print("📥 /search/history endpoint hit")
        history = get_history()
        print(f"✅ Loaded {len(history)} entries")
        return {"history": history}
    except Exception as e:
        logging.exception("History retrieval failed")
        return {"history": [], "error": str(e)}