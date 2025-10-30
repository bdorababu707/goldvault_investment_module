from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from app.core.security import get_current_admin
from app.db.mongo.mongodb import find_one
from app.models.base import OutModel
from app.schemas.investment import CreateInvestmentPlan, CreateInvestmentSubscription, UpdateInvestmentPlan
from app.services.plans.plans import PlanService

router = APIRouter()

@router.post("/create")
async def create_investment_plan(
    request: CreateInvestmentPlan,
    current_admin = Depends(get_current_admin)
):
    try:
        result = await PlanService.create_investment_plan(request, current_admin)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to create investment plan",
            data=str(e),
        )
    
@router.get("/all")
async def get_investment_plans(current_admin=Depends(get_current_admin)):
    try:
        result = await PlanService.get_investment_plans(current_admin)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=400,
            comment="Failed to fetch investment plans",
            data=str(e),
        )

@router.get("/id")
async def get_plan_by_id(
    plan_id: str,
    current_admin=Depends(get_current_admin)
    ):
    try:
        result = await PlanService.get_plan_by_id(plan_id, current_admin)
        return OutModel(**result)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=400,
            comment="Failed to fetch investment plan",
            data=str(e),
        )
    


@router.patch("/update-plan")
async def update_investment_plan(
    plan_id: str,
    update_data: UpdateInvestmentPlan,
    current_admin=Depends(get_current_admin)
):
    try:
        update_dict = update_data.model_dump(exclude_none=True)

        response = await PlanService.update_investment_plan(plan_id, update_dict, current_admin)
        return OutModel(**response)

    except Exception as err:
        return OutModel(
            status="error",
            status_code=500,
            comment="Something went wrong while updating the plan",
            data=str(err)
        )
