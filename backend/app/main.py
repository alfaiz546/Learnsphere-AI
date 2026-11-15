from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LearnSphere AI API",
    description="Interactive learning platform backend with autonomous AI mentor agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing LearnSphere AI database...")
    try:
        from app.database.init_db import init_db
        init_db()
        logger.info("Database initialized & verified.")
    except Exception as e:
        logger.error(f"Startup database initialization error: {e}")

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "LearnSphere AI", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "LearnSphere AI API is running", "docs": "/docs"}
