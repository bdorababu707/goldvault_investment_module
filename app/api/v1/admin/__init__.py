from fastapi import APIRouter
from .admin_auth import router as admin_auth_router
from .user_service import router as user_service_router
from .investment import router as investment_router
from .plans import router as plans_router
from .subscriptions import router as subscriptions_router
from .inventory import router as inventory_router

router = APIRouter(
    prefix="/admin",
)

router.include_router(admin_auth_router)
router.include_router(user_service_router)
router.include_router(inventory_router)
router.include_router(plans_router)
router.include_router(subscriptions_router)
router.include_router(investment_router)