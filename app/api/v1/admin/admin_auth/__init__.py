from fastapi import APIRouter
from .auth import router as admin_router

router = APIRouter(prefix="/auth", tags=["Admin Auth"])

router.include_router(admin_router)