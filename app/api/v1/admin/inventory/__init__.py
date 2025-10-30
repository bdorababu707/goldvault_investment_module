from fastapi import APIRouter
from .inventory import router as inventory_router

router = APIRouter(prefix="/inventory", tags=["Inventory"])

router.include_router(inventory_router)