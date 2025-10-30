from datetime import datetime, timedelta
from app.services.inventory.inventory import InventoryService
from app.services.subscriptions.subscriptions import SubscriptionService
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
from app.utils.email_service.email import EmailService, InvestmentConfirmationTemplate

logger = get_logger(__name__)

class InvestmentService:

    @staticmethod
    async def create_investment_entry(request: object, current_admin: dict):
        try:
            # 1️⃣ Validate Subscription
            subscription = await find_one(
                settings.DB_TABLE.SUBSCRIPTIONS, {"uuid": request.subscription_id}
            )
            if not subscription:
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": f"Subscription not found with id: {request.subscription_id}",
                    "data": None,
                }

            # 2️⃣ Ensure subscription belongs to user
            if subscription["user_id"] != request.user_id:
                return {
                    "status": "error",
                    "status_code": 400,
                    "comment": "Subscription does not belong to given user_id",
                    "data": None,
                }

            # 3️⃣ Extract plan info
            plan = subscription["metadata"]["plan_details"]

            # 4️⃣ Compute allowed deposit range
            start_date = datetime.strptime(subscription["plan_start_date"], "%d-%m-%Y").date()
            payment_date = datetime.strptime(request.deposit_date, "%d-%m-%Y").date()

            # Determine expected deposit date (next month * 30)
            entries_response = await SubscriptionService.get_user_subscription_transactions(
                user_id=request.user_id,
                subscription_id=request.subscription_id,
            )

            months_passed = (
                len(entries_response["data"])
                if entries_response["status"] == "success" and entries_response["data"]
                else 0
            )

            expected_date = start_date + timedelta(days=months_passed * 30)
            relaxation_days = plan.get("relaxation_days", 0)
            allowed_last_date = expected_date + timedelta(days=relaxation_days)

            # 5️⃣ Check on-time payment
            on_time = payment_date <= allowed_last_date
            min_amount = plan.get("minimum_investment_amount", 0)
            if request.amount_invested < min_amount:
                on_time = False

            # 6️⃣ Determine if bonus already credited for this month
            payment_month = payment_date.month
            payment_year = payment_date.year

            existing_bonus_entry = await find_one(
                settings.DB_TABLE.INVESTMENT_ENTRIES,
                {
                    "subscription_id": request.subscription_id,
                    "user_id": request.user_id,
                    "is_bonus_credited": True,
                    "$expr": {
                        "$and": [
                            {"$eq": [{"$month": {"$dateFromString": {"dateString": "$deposit_date"}}}, payment_month]},
                            {"$eq": [{"$year": {"$dateFromString": {"dateString": "$deposit_date"}}}, payment_year]},
                        ]
                    },
                },
            )

            # ✅ Bonus logic
            bonus_earned = 0
            is_bonus_credited = False
            if on_time and not existing_bonus_entry:
                bonus_earned = round(plan["bonus_percentage"] / 12, 2)
                is_bonus_credited = True

            created_by = {"email": current_admin["email"]}

            # 7️⃣ Build investment entry
            entry = InvestmentEntry(
                uuid=await generate_uuid(),
                user_id=request.user_id,
                subscription_id=request.subscription_id,
                deposit_date=request.deposit_date,
                amount_invested=request.amount_invested,
                gold_rate=request.gold_rate,
                grams_purchased=request.grams_purchased,
                payment_method=request.payment_method,
                transaction_reference=request.transaction_ref,
                payment_proof_url=request.payment_proof_url,
                bonus_earned=bonus_earned,
                is_bonus_eligible=on_time,
                is_bonus_credited=is_bonus_credited,  # ✅ added field
                remarks=request.remarks,
                metadata={"created_by": created_by},
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )

            # 8️⃣ Insert entry
            await insert_one(settings.DB_TABLE.INVESTMENT_ENTRIES, entry.model_dump())

            # 9️⃣ Update inventory
            update_payload = {
                "$inc": {
                    "invested_amount": request.amount_invested,
                    "gold_grams_24k": request.grams_purchased,
                },
                "$set": {"updated_at": int(time.time())},
            }

            if is_bonus_credited and bonus_earned > 0:
                update_payload["$inc"]["bonus_percentage_earned"] = bonus_earned

            await update_one(
                settings.DB_TABLE.INVENTORY,
                {"subscription_id": request.subscription_id},
                update_payload,
            )

            # 🔁 Fetch Updated Inventory
            updated_inventory = await find_one(
                collection=settings.DB_TABLE.INVENTORY,
                query={"subscription_id": request.subscription_id},
            )

            # 1️⃣0️⃣ Email notification
            try:
                user = await find_one(settings.DB_TABLE.USERS, {"uuid": request.user_id})
                if user and user.get("email"):
                    await InvestmentConfirmationTemplate.send_investment_confirmation(
                        to_email=user["email"],
                        user_name=f"{user.get("full_name")}".strip(),
                        plan_name=plan["plan_name"],
                        payment_amount=request.amount_invested,
                        grams_purchased=request.grams_purchased,
                        deposit_date=request.deposit_date,
                        currency=updated_inventory.get("currency", "AED"),
                        total_invested=updated_inventory.get("invested_amount", 0),
                        total_grams=updated_inventory.get("gold_grams_24k", 0),
                    )
            except Exception as mail_err:
                logger.warning(f"Email send failed: {mail_err}")

            return {
                "status": "success",
                "status_code": 200,
                "comment": "Investment entry created successfully",
                "data": entry.model_dump(),
            }

        except Exception as e:
            logger.error(f"Error creating investment entry: {str(e)}")
            return {
                "status": "error",
                "status_code": 400,
                "comment": "Something went wrong",
                "data": str(e),
            }
