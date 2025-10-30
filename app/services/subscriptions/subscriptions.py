import asyncio
from datetime import datetime, timedelta
from app.services.inventory.inventory import InventoryService
from app.utils.common import generate_uuid
from app.models.user import User
from app.db.mongo.mongodb import find_many, find_one, insert_one, update_one
import time
from icecream import ic
from app.core.security import create_access_token
from app.schemas.investment import CreateInvestmentPlan
from app.models.investment import InvestmentEntry, InvestmentPlan, UserInvestmentSubscription
from app.models.inventory import InvestmentInventory
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.email_service.email import SubscriptionEmailTemplate

logger = get_logger(__name__)

class SubscriptionService:

    @staticmethod
    async def create_subscription_for_user(user_id: str, plan_id: str, plan_start_date: str, current_admin: dict):
        """
        Creates a subscription for a user under a specific investment plan.
        Also creates a corresponding investment inventory for that subscription.
        """
        try:
            # Validate user
            user = await find_one(
                collection=settings.DB_TABLE.USERS,
                query={"uuid": user_id},
                projection={"_id": 0}
            )
            if not user:
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": "User not found",
                    "data": None
                }

            # Validate plan
            plan = await find_one(
                collection=settings.DB_TABLE.AVAILABLE_INVESTMENT_PLANS,
                query={"uuid": plan_id, "status": "ACTIVE"},
                projection={"_id": 0}
            )
            if not plan:
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": "Plan not found or inactive",
                    "data": None
                }

            # Create user subscription
            subscription = UserInvestmentSubscription(
                uuid=await generate_uuid(),
                user_id=user_id,
                plan_id=plan_id,
                plan_start_date=plan_start_date,
                metadata={"plan_details":plan},
                status="ACTIVE",
                created_at=int(time.time()),
                updated_at=int(time.time())
            )

            await insert_one(
                collection=settings.DB_TABLE.SUBSCRIPTIONS,
                document=subscription.model_dump()
            )

            # Create inventory linked to this subscription
            try:
                inventory_result = await InventoryService.create_investment_inventory_for_subscription(
                    user_id=user_id,
                    subscription_id=subscription.uuid
                )
                logger.info(f"Inventory created for subscription {subscription.uuid}: {inventory_result}")
            except Exception as e:
                logger.error(f"Failed to create inventory for subscription {subscription.uuid}: {str(e)}")

            # Send subscription confirmation email asynchronously
            try:
                asyncio.create_task(
                    SubscriptionEmailTemplate.send_subscription_created_email(
                        user_email=user["email"],
                        full_name=user.get("full_name", "User"),
                        plan=plan
                    )
                )
            except Exception as email_err:
                logger.error(f"Failed to send subscription created email: {str(email_err)}")


            return {
                "status": "success",
                "status_code": 201,
                "comment": "Subscription created successfully",
                "data": subscription.model_dump()
            }

        except Exception as e:
            logger.error(f"Error while creating subscription for user {user_id}: {str(e)}")
            return {
                "status": "error",
                "status_code": 500,
                "comment": "Internal server error while creating subscription",
                "data": str(e)
            }

    @staticmethod
    async def get_user_subscription_transactions(user_id: str, subscription_id: str):
        """Fetch all previous investments for a user's subscription"""
        try:
            entries = await find_many(
                collection=settings.DB_TABLE.INVESTMENT_ENTRIES,
                query={"subscription_id": subscription_id},projection={"_id":0}
            )

            if not entries:
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": f"No previous investment entries found for subscription id: {subscription_id}",
                    "data": None,
                }

            return {
                "status": "success",
                "status_code": 200,
                "comment": "Successfully fetched investment entries",
                "data": entries,
            }

        except Exception as e:
            logger.error(
                f"Error while fetching investment entries for user-id: {user_id}, "
                f"subscription-id: {subscription_id}, error: {str(e)}"
            )
            return {
                "status": "error",
                "status_code": 400,
                "comment": "Something went wrong",
                "data": str(e),
            }

    @staticmethod
    async def get_user_subscriptions(user_id: str,current_admin: dict):
        try:
            investment_plans = await find_many(collection=settings.DB_TABLE.SUBSCRIPTIONS, query={"user_id": user_id}, projection={"_id": 0})

            return {
                "status": "success",
                "status_code": 200,
                "comment": "Investment plans fetched successfully",
                "data": investment_plans or []
            }
        
        except Exception as e:
            logger.error(f"Error while fetching investment plans for user-id: {user_id}, error: {str(e)}")
            return {
                "status":"error",
                "status_code": 400,
                "comment": "something went wrong",
                "data": str(e)
            }
        
    