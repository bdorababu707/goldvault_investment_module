from fastapi import APIRouter
from .plans import router as plans_router

router = APIRouter(prefix="/plans", tags=["Plans"])

router.include_router(plans_router)