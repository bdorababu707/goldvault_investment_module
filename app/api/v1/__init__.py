from fastapi import APIRouter
from .admin import router as admin_router
from .common import router as common_router

router = APIRouter()

router.include_router(common_router)
router.include_router(admin_router)