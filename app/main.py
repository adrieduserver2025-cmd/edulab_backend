import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.firebase import initialize_firebase
from app.api.v1.router import router as api_v1_router
from app.database.base import Base
from app.database.session import engine

# Importar modelos para registrarlos en Base.metadata
from app.users.models import User
from app.students.models import StudentProfile

# Explicitly import all models to register them with Base.metadata on startup (commented out Phase 3/4 models)
# from app.users.models import User
# from app.students.models import StudentProfile
# from app.programs.models import Program
# from app.applications.models import Application
# from app.documents.models import Document

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing Firebase Admin SDK...")
    initialize_firebase()

    if settings.DEV_MODE:
        logger.info("🔧 DEV_MODE active: Ensuring database tables exist...")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to auto-initialize database tables: {e}")
            logger.warning("Make sure PostgreSQL is running, or DATABASE_URL is configured correctly.")

    yield
    # Shutdown actions (if any)
    logger.info("Stopping EDULAB Application Server...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="EDULAB - Intelligent Educational Opportunities SaaS API",
    version="1.0.0",
    lifespan=lifespan
)

# Apply CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register main API router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Standard JSON endpoint for systems monitoring.
    """
    db_ok = False
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB error: {e}")

    return {
        "status": "healthy" if db_ok else "degraded",
        "project": settings.PROJECT_NAME,
        "database": "connected" if db_ok else "disconnected",
        "firebase_mode": "mock_dev" if not settings.FIREBASE_CREDENTIALS_JSON and not settings.FIREBASE_CREDENTIALS_PATH else "production"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
