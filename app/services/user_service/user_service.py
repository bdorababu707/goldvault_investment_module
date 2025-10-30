import asyncio
from app.utils.common import generate_uuid
from app.models.user import User
from app.db.mongo.mongodb import find_many, find_one, insert_one, update_one
import time
from icecream import ic
from app.core.security import create_access_token
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.email_service.email import UserEmailTemplate

logger = get_logger(__name__)

class UserService:

    @staticmethod
    async def create_user(request:object, current_admin: dict):
        try:
            user = await find_one(collection=settings.DB_TABLE.USERS, query={"email": request.email})

            if user:
                return {
                    "status":"error",
                    "status_code":400,
                    "comment": "User with this email already exist",
                    "data": None
                }
            
            kyc_docs_dict = request.kyc_documents.model_dump() if request.kyc_documents else None
            created_by = {
                "email": current_admin['email']
            }
            user_document = User(
                uuid=await generate_uuid(),
                email=request.email,
                phone_number=request.phone_number,
                country_code=request.country_code,
                country=request.country,
                full_name=request.full_name,
                date_of_birth=request.date_of_birth,
                nationality=request.nationality,
                country_of_birth=request.country_of_birth,
                country_of_residence=request.country_of_residence,
                full_address=request.full_address,
                kyc_documents=kyc_docs_dict,
                metadata={"created_by": created_by},
                created_at=int(time.time()),
                updated_at=int(time.time())
            )

            await insert_one(collection=settings.DB_TABLE.USERS, document=user_document.model_dump())

            # Send welcome email asynchronously
            try:
                asyncio.create_task(
                    UserEmailTemplate.send_account_created_email(
                        user_email=request.email,
                        full_name=request.full_name,
                    )
                )
            except Exception as email_err:
                logger.error(f"Failed to send account creation email: {str(email_err)}")

            return {
                "status":"success",
                "status_code":201,
                "comment": "User created successfully",
                "data": user_document.model_dump()
            }
            

        except Exception as e:
            logger.error(f"Error while creating user, error : {str(e)}")
            return {
                "status":"error",
                "status_code":400,
                "comment": "Something went wrong",
                "data": str(e)
            }
        
    @staticmethod
    async def get_all_users(current_admin: dict):
        try:
            users = await find_many(collection=settings.DB_TABLE.USERS, query={}, projection={"_id":0})

            if not users:
                return {"status": "error",
                        "status_code": 400,
                        "comment": "No users found",
                        "data": None
                    }
            
            return {
                "status": "success",
                "status_code": 200,
                "comment": "Users fetched successfully",
                "data": users
            }
        
        except Exception as e:
            logger.error(f"Error while fetching users, error : {str(e)}")
            return {
                "status":"error",
                "status_code":400,
                "comment": "Something went wrong",
                "data": str(e)
            }
        
    @staticmethod
    async def get_user_by_id(user_id: str, current_admin: dict):
        try:
            user = await find_one(collection=settings.DB_TABLE.USERS, query={"uuid": user_id}, projection={"_id":0})

            if not user:
                return {
                    "status": "error",
                    "status_code": 404,
                    "comment": "User not found",
                    "data": None
                }
            
            return {
                "status":"success",
                "status_code":200,
                "comment":"User fetched successfully",
                "data":user
            }
        
        except Exception as e:
            logger.error(f"Error while fetching user details by id: {user_id}, error: {str(e)}")
            return {
                    "status": "error",
                    "status_code": 404,
                    "comment": "something went wrong",
                    "data": str(e)
                }