from fastapi import APIRouter
from .test_common import router as health_router
from . file_upload import router as file_upload_router


router = APIRouter()

router.include_router(health_router)
router.include_router(file_upload_router)
