from app.services.inventory.inventory import InventoryService
from app.utils.common import generate_uuid
from app.models.user import User
from app.db.mongo.mongodb import find_many, find_one, insert_one, update_one
import time
from icecream import ic
from app.core.security import create_access_token
from app.schemas.investment import CreateInvestmentPlan
from app.models.investment import InvestmentPlan, UserInvestmentSubscription
from app.models.inventory import InvestmentInventory
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class PlanService:

    @staticmethod
    async def create_investment_plan(request:object, current_admin: dict):
        try:
            created_by = {
                "email":current_admin["email"]
            }

            investment_plan = InvestmentPlan(
                uuid=await generate_uuid(),
                plan_name=request.plan_name,
                description=request.description,
                bonus_percentage=request.bonus_percentage,
                relaxation_days=request.relaxation_days,
                minimum_investment_amount=request.minimum_investment_amount,
                metadata={"created_by":created_by},
                status="ACTIVE",
                created_at=int(time.time()),
                updated_at=int(time.time())
            )

            await insert_one(collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS, document=investment_plan.model_dump())
        
            return {
                "status": "success",
                "status_code": 201,
                "comment": "Investment plan created successfully",
                "data": investment_plan.model_dump()
            }

        except Exception as e:
            logger.error(f"Error while creating investment plan, error: {str(e)}")
            return {
                "status":"error",
                "status_code": 400,
                "comment": "something went wrong",
                "data": str(e)
            }
        
    @staticmethod
    async def get_investment_plans(current_admin: dict):
        try:
            investment_plans = await find_many(collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS, query={"status": "ACTIVE"}, projection={"_id": 0})

            return {
                "status": "success",
                "status_code": 200,
                "comment": "Investment plans fetched successfully",
                "data": investment_plans or []
            }
        
        except Exception as e:
            logger.error(f"Error while fetching investment plans, error: {str(e)}")
            return {
                "status":"error",
                "status_code": 400,
                "comment": "something went wrong",
                "data": str(e)
            }

    @staticmethod
    async def get_plan_by_id(plan_id: str, current_admin: dict):
        try:
            plan = await find_many(collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS, query={"uuid": plan_id,"status": "ACTIVE"}, projection={"_id": 0})

            if not plan:
                return {
                "status": "error",
                "status_code": 404,
                "comment": "Investment plan not found or not active",
                "data": None
                }

            return {
                "status": "success",
                "status_code": 200,
                "comment": "Investment plan fetched successfully",
                "data": plan
            }
        
        except Exception as e:
            logger.error(f"Error while fetching investment plan by id: {plan_id}, error: {str(e)}")
            return {
                "status":"error",
                "status_code": 400,
                "comment": "something went wrong",
                "data": str(e)
            }
        

    @staticmethod
    async def update_investment_plan(plan_id: str, update_data: dict, current_admin: dict):
        """Update an existing investment plan."""
        try:
            # Clean data (remove None values)
            update_data = {k: v for k, v in update_data.items() if v is not None}
            if not update_data:
                return {
                    "status":"error",
                    "status_code":400,
                    "comment":"No valid data provided for update",
                    "data":""
                }

            # Fetch current plan
            plan = await find_one(
                collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS,
                query={"uuid": plan_id},
                projection={"_id": 0}
            )

            if not plan:
                return {
                    "status":"error",
                    "status_code":404,
                    "comment":"Investment plan not found",
                    "data":""
                }

            # Add updated_by and updated_at
            update_data["metadata.last_updated_by"] = {"email": current_admin.get("email")}
            update_data["updated_at"] = int(time.time())

            logger.info(f"Updating investment plan {plan_id} with data: {update_data}")

            # Perform DB update
            result = await update_one(
                collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS,
                query={"uuid": plan_id},
                update={"$set": update_data}
            )

            if not result.get("modified_count"):
                return {
                    "status":"error",
                    "status_code":400,
                    "comment":"No changes were made to the plan",
                    "data":""
                }

            # Fetch updated plan
            updated_plan = await find_one(
                collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS,
                query={"uuid": plan_id},
                projection={"_id": 0}
            )

            return {
                "status":"success",
                "status_code":200,
                "comment":"Investment plan updated successfully",
                "data":updated_plan
            }

        except Exception as e:
            logger.error(f"Error updating investment plan {plan_id}: {str(e)}")
            return {
                "status":"error",
                "status_code":400,
                "comment":"Failed to update investment plan",
                "data":str(e)
            }
