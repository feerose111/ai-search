from fastapi import FastAPI
from backend_second.api.routes import search
from backend_second.utils.feature.logger import setup_logger
from backend_second.utils.feature.history import history_service


app = FastAPI()
logger = setup_logger()


app.include_router(search.router)

if history_service:
    logger.info("Starting history service consumer in background")
    history_service.start_consumer()

@app.on_event("startup")
def list_routes():
    from fastapi.routing import APIRoute
    logger.info("✅ Registered Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            logger.info(f"{route.path} → {route.endpoint.__name__}")

@app.on_event("shutdown")
def shutdown_event():
    if hasattr(search, 'log_executor'):
        search.log_executor.shutdown(wait=False)
    if hasattr(search, 'history_service') and search.history_service:
        search.history_service.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)


