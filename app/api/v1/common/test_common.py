from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.db.mongo.mongodb import get_database
from app.core.logging import get_logger

router = APIRouter(tags=["health"])

# Get logger
logger = get_logger(__name__)

@router.get("/test-common")
async def test_common():
    """Check if the application is running and connected to MongoDB"""
    try:
        # Get database instance
        db = get_database()
        
        # Ping MongoDB to check connection
        is_connected = await db.command("ping")
        
        if is_connected:
            return {
                "status": "healthy",
                "database": "connected",
                "mode": "development" if settings.is_development() else "production",
                "version": settings.APP.VERSION
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )
