from fastapi import FastAPI
from backend.api.routes import admin, search
from backend.utils.feature.logger import setup_logger

app = FastAPI()
logger = setup_logger()

app.include_router(admin.router)
app.include_router(search.router)

@app.on_event("startup")
def list_routes():
    from fastapi.routing import APIRoute
    logger.info("✅ Registered Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            logger.info(f"{route.path} → {route.endpoint.__name__}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


