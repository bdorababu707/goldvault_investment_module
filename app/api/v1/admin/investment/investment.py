from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from app.core.security import get_current_admin
from app.db.mongo.mongodb import find_one
from app.models.base import OutModel
from app.schemas.investment import CreateInvestmentPlan, CreateInvestmentSubscription, CreateMonthlyInvestment
from app.services.investment.investment import InvestmentService

router = APIRouter()

    

@router.post("/investment-entry-for-subscription")
async def investment_entry_for_subscription(request: CreateMonthlyInvestment, current_admin = Depends(get_current_admin)):
    try:
        result = await InvestmentService.create_investment_entry(request, current_admin)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=400,
            comment="failed to create investment entry",
            data=str(e)
        )
    
