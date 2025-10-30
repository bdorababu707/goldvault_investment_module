from fastapi import APIRouter
from .investment import router as investment_router

router = APIRouter(prefix="/investment", tags=["Investment"])

router.include_router(investment_router)