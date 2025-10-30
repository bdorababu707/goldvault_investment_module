from app.db.mongo.mongodb import find_one, insert_one
from app.models.inventory import InvestmentInventory
from app.utils.common import generate_uuid
from app.core.config import settings
from app.core.logging import get_logger
import time

logger = get_logger(__name__)

class InventoryService:

    @staticmethod
    async def create_investment_inventory_for_subscription(user_id: str, subscription_id: str):
        """
        Creates a new investment inventory linked to a specific user subscription.
        """
        try:
            logger.info(f"Creating investment inventory for user: {user_id}, subscription: {subscription_id}")

            # Validate user existence
            user = await find_one(collection=settings.DB_TABLE.USERS, query={"uuid": user_id})
            if not user:
                logger.error(f"User not found: {user_id}")
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": "User not found",
                    "data": None
                }

            # Validate subscription existence
            subscription = await find_one(
                collection=settings.DB_TABLE.SUBSCRIPTIONS,
                query={"uuid": subscription_id}
            )
            if not subscription:
                logger.error(f"Subscription not found: {subscription_id}")
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": "Subscription not found",
                    "data": None
                }

            # Create inventory
            inventory = InvestmentInventory(
                uuid=await generate_uuid(),
                user_id=user_id,
                subscription_id=subscription_id,
                gold_grams_24k=0,
                invested_amount=0,
                status="ACTIVE",
                currency="AED",
                created_at=int(time.time()),
                updated_at=int(time.time())
            )

            # Insert into DB
            await insert_one(
                collection=settings.DB_TABLE.INVENTORY,
                document=inventory.model_dump()
            )

            logger.info(f"Inventory created successfully for subscription {subscription_id}")
            return {
                "status": "success",
                "status_code": 201,
                "comment": "Inventory created successfully",
                "data": inventory.model_dump()
            }

        except Exception as e:
            logger.error(f"Error creating inventory for subscription {subscription_id}: {e}")
            return {
                "status": "error",
                "status_code": 500,
                "comment": "Internal server error while creating inventory",
                "data": str(e)
            }

    @staticmethod
    async def get_user_subscription_inventory(user_id: str, subscription_id: str):
        try:
            subscription_inventory = await find_one(collection=settings.DB_TABLE.INVENTORY, query={"user_id": user_id, "subscription_id": subscription_id}, projection={"_id":0})
            return {
                "status": "success",
                "status_code":200,
                "comment":"User subscription inventory fetched successfully",
                "data": subscription_inventory
            }
        except Exception as e:
            logger.error(f"error while fetching user subscription inventory with user-id: {user_id}, subscription-id: {subscription_id}, error: {str(e)}")
            return {
                "status": "error",
                "status_code": 400,
                "comment": "error while fetching user subscription inventory",
                "data": str(e)
            }