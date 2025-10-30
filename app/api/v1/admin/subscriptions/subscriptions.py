from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from app.core.security import get_current_admin
from app.db.mongo.mongodb import find_one
from app.models.base import OutModel
from app.schemas.investment import CreateInvestmentPlan, CreateInvestmentSubscription, CreateMonthlyInvestment
from app.services.investment.investment import InvestmentService
from app.services.subscriptions.subscriptions import SubscriptionService

router = APIRouter()

    
    
@router.post("/create-user-subscription")
async def create_user_investment_subscription(request: CreateInvestmentSubscription, current_admin=Depends(get_current_admin)):
    try:
        result = await SubscriptionService.create_subscription_for_user(request.user_id, request.plan_id, request.plan_start_date, current_admin)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=400,
            comment="Failed to fetch investment plans",
            data=str(e),
        )  
    

@router.get("/user-id")
async def get_user_subscriptions(user_id: str, current_admin=Depends(get_current_admin)):
    try:
        result = await SubscriptionService.get_user_subscriptions(user_id, current_admin)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=400,
            comment="Failed to fetch investment plans",
            data=str(e),
        )
    
@router.get("/transactions")
async def get_investment_subscription_transactions(
    user_id: str,
    subscription_id: str,
    current_admin=Depends(get_current_admin)
):
    try:
        result = await SubscriptionService.get_user_subscription_transactions(user_id,subscription_id)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="success",
            status_code=400,
            comment="Error while fetching investment subscription transactions",
            data=str(e)
        )
    
