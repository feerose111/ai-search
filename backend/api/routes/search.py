from fastapi import APIRouter, HTTPException, Query
from backend.utils.elastic_search.es_client import get_es
from backend.search.query_milvus import search_documents
from backend.utils.parser.query_parser import parse_query
from backend.utils.feature.logger import setup_logger  
import logging
from backend.utils.feature.history import get_history, log_query_to_history

router = APIRouter()

# === Logging Setup ===
setup_logger()
@router.get("/search")
def search(q: str, top_k: int = Query(5, ge=1, le=20)):
    try:
        parsed = parse_query(q)
        results = search_documents(parsed["raw_query"], parsed, top_k=top_k)

        # Log to Elasticsearch before returning
        es_client = get_es()
        log_query_to_history(es_client, q, parsed)

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
