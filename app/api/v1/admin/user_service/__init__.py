from fastapi import APIRouter
from .user_service import router as user_service_router

router = APIRouter(prefix="/user-service", tags=["User Service"])

router.include_router(user_service_router)