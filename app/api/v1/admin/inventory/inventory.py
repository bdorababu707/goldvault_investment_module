from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from app.core.security import get_current_admin
from app.db.mongo.mongodb import find_one
from app.models.base import OutModel
from app.schemas.investment import CreateInvestmentPlan, CreateInvestmentSubscription, CreateMonthlyInvestment
from app.services.inventory.inventory import InventoryService
from app.services.investment.investment import InvestmentService

router = APIRouter()

@router.get("/user-subscription-inventory")
async def get_user_subscription_inventory(user_id: str,
                                          subscription_id: str,
                                          current_admin=Depends(get_current_admin)):
    try:
        response = await InventoryService.get_user_subscription_inventory(user_id, subscription_id)
        return OutModel(**response)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=400,
            comment="error while fetching user subscription inventory",
            data=str(e)
        )