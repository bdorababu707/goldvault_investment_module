from fastapi import APIRouter
from .subscriptions import router as investment_router

router = APIRouter(prefix="/subscriptions", tags=["Plan subscriptions"])

router.include_router(investment_router)