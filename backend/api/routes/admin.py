from fastapi import APIRouter, UploadFile, File, HTTPException, Request, status,Query
from backend.search.upsert_milvus import upsert_ingestion
from backend.utils.config import COLLECTION_NAME
from backend.utils.db.source_db import (
    get_source_file_count, get_dataset_info, get_recent_errors,
    get_milvus_count, get_es_count)
from backend.embedding.producer import get_buffer_count
from backend.utils.feature.logger import setup_logger
import platform
import psutil
from backend.utils.io.file_processor import process_file
import json

logger = setup_logger()

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/upsert")
async def upsert_json(request: Request):
    try:
        data = await request.json()
        logger.info(f"Upsert request received ")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON body | error={str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not data:
        logger.error("Empty data received in upsert request")
        raise HTTPException(status_code=400, detail="No input data provided")

    if isinstance(data, dict) or isinstance(data, list):
        try:
            success = upsert_ingestion(data)
            logger.info(f"Upsert completed | status={'success' if success else 'failure'}")
            return {"status": "success" if success else "error"}
        except Exception as e:
            logger.error(f"Upsert ingestion failed | error={str(e)}")
            raise HTTPException(status_code=500, detail=f"Upsert failed: {str(e)}")
    else:
        logger.error(f"Invalid data format received ")
        raise HTTPException(400, "JSON must be an object or list")

@router.post("/upsert/file")
async def upsert_file(file: UploadFile = File(...)):
    logger.info(f"File upload initiated ")
    if not file:
        logger.error("No file uploaded")
        raise HTTPException(400, "No file uploaded")

    try:
        content = await file.read()
        documents = process_file(content, file.content_type)
        doc_count = len(documents) if isinstance(documents, list) else 1
        logger.info(f"File processed successfully ")

        success = upsert_ingestion(documents)
        logger.info(f"File upsert completed | status={'success' if success else 'failure'}")
        return {
            "status": "success" if success else "error",
            "documents_processed": doc_count
        }
    except Exception as e:
        logger.error(f"File processing failed | filename={file.filename} error={str(e)}")
        raise HTTPException(400, detail=f"Processing error: {str(e)}")

@router.get("/count")
async def get_data_count():
    try:
        source_count = get_source_file_count()
        buffer_count = get_buffer_count()
        milvus_count = get_milvus_count()
        es_count = get_es_count()
        logger.info(
            f"Data counts retrieved | "
            f"source={source_count} buffer={buffer_count} "
            f"milvus={milvus_count} es={es_count}"
        )
        return {
                "actual_count": source_count + buffer_count,
                "milvus_count": milvus_count,
                "elasticsearch_count": es_count,
                "source_file_count": source_count,
                "buffer_count": buffer_count
        }
    except Exception as e:
        logger.error(f"Failed to retrieve counts | error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error retrieving counts: {str(e)}"
        )

@router.get("/errors")
def get_errors():
    try:
        errors = get_recent_errors()
        logger.info(f"Retrieved recent errors | count={len(errors)}")
        return {"errors": errors}
    except Exception as e:
        logger.error(f"Failed to retrieve recent errors | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving errors: {str(e)}")

@router.get("/stats")
def get_stats():
    try:
        dataset_info = get_dataset_info()
        stats = {
            "indexing_mode": "Kafka → Milvus",
            "dataset": dataset_info,
            "collection": COLLECTION_NAME,
            "system": {
                "os": platform.system(),
                "cpu_cores": psutil.cpu_count(logical=False),
                "cpu_threads": psutil.cpu_count(logical=True),
                "memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            },
        }
        logger.info(f"System stats retrieved ")
        return stats
    except Exception as e:
        logger.error(f"Failed to retrieve system stats | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")
