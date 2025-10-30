from app.core.security import decode_jwt_token, hash_password, verify_password
from app.db.mongo.mongodb import find_one, update_one
from jwt import PyJWTError
from app.core.security import create_verification_token
from app.models.admin import Admin, DepartmentAdmin, SuperAdmin
from app.models.base import OutModel
from app.schemas.admin import CreateAdmin, CreateDepartmentAdmin, CreateSuperAdmin
from app.utils.common import generate_uuid
from app.models.user import User
from app.db.mongo.mongodb import find_one, insert_one, update_one
import time
from icecream import ic
from app.core.security import create_access_token
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuthService:

    @staticmethod
    async def create_super_admin(payload:CreateSuperAdmin, secret_key: str) -> OutModel:
        """
        Create a super admin after validating secret key and duplicates.
        """
        # Verify secret key
        if secret_key != settings.SECRET_KEYS.SUPER_ADMIN_SECRET_KEY:
            logger.warning("Invalid secret key for Super Admin creation")
            return OutModel(
                status="failure",
                status_code=403,
                comment="Invalid secret key",
                data="",
            )

        # Check duplicate email
        existing_email = await find_one(
            settings.DB_TABLE.ADMINS, {"email": payload.email}
        )
        if existing_email:
            logger.warning(f"Duplicate super admin email: {payload.email}")
            return OutModel(
                status="failure",
                status_code=400,
                comment="Email already exists",
                data="",
            )

        # Check duplicate phone
        existing_phone = await find_one(
            settings.DB_TABLE.ADMINS, {"phone_number": payload.phone_number}
        )
        if existing_phone:
            logger.warning(f"Duplicate super admin phone: {payload.phone_number}")
            return OutModel(
                status="failure",
                status_code=400,
                comment="Phone number already exists",
                data="",
            )

        now = int(time.time())
        # Prepare admin data
        admin_data = SuperAdmin(
            uuid=await generate_uuid(),
            firstname=payload.firstname,
            surname=payload.surname,
            email=payload.email,
            country=payload.country,
            country_code=payload.country_code,
            phone_number=payload.phone_number,
            password=await hash_password(payload.password),
            user_type="SUPER_ADMIN",
            created_at=now,
            updated_at=now,
        ).model_dump()

        try:
            # Insert into DB
            logger.info(f"Creating super admin: {payload.email}")
            await insert_one(settings.DB_TABLE.ADMINS, admin_data)
            logger.info(f"Super admin created: {payload.email}")

            admin_data.pop("_id", None)
            admin_data.pop("password", None)
            return OutModel(
                status="success",
                status_code=201,
                comment="Super admin created successfully",
                data=admin_data,
            )
        except Exception as e:
            logger.error(f"Error creating super admin: {payload.email}: {str(e)}")
            return OutModel(
                status="error",
                status_code=500,
                comment="Failed to create super admin",
                data=str(e),
            )

    @staticmethod
    async def create_department_admin(payload:CreateDepartmentAdmin, current_admin:dict) -> OutModel:
        # Check if requester is SUPER_ADMIN
        if current_admin["user_type"] != "SUPER_ADMIN":
            logger.warning(f"Unauthorized dept-admin creation attempt by {current_admin['email']}")

            return OutModel(
                status="failure",
                status_code=403,
                comment="Access Denied. You dont have permission to create Department Admins",
                data=""
            )

        # Check duplicate email
        existing_email = await find_one(
            settings.DB_TABLE.ADMINS, {"email": payload.email}
        )
        if existing_email:
            logger.warning(f"Duplicate dept-admin email: {payload.email}")
            return OutModel(
                status="failure",
                status_code=400,
                comment="Email already exists",
                data=""
            )

        # Check duplicate phone
        existing_phone = await find_one(
            settings.DB_TABLE.ADMINS, {"phone_number": payload.phone_number}
        )
        if existing_phone:
            logger.warning(f"Duplicate dept-admin phone: {payload.phone_number}")
            return OutModel(
                status="failure",
                status_code=400,
                comment="Phone number already exists",
                data=""
            )

        now = int(time.time())
        # Prepare dept-admin data
        dept_admin_data = DepartmentAdmin(
            uuid=await generate_uuid(),
            firstname=payload.firstname,
            surname=payload.surname,
            email=payload.email,
            country=payload.country,
            country_code=payload.country_code,
            phone_number=payload.phone_number,
            password=await hash_password(payload.password),
            user_type="DEPT_ADMIN",
            created_by=current_admin["uuid"],
            created_at=now,
            updated_at=now,
        ).model_dump()

        try:
            # Insert into DB
            await insert_one(settings.DB_TABLE.ADMINS, dept_admin_data)

            dept_admin_data.pop("_id", None)
            dept_admin_data.pop("password", None)
            return OutModel(
                status="success",
                status_code=201,
                comment="Department Admin created successfully",
                data=dept_admin_data
            )
        except Exception as e:
            logger.error(f"Error creating department admin: {str(e)}")
            return OutModel(
                status="error",
                status_code=500,
                comment="Failed to create Department Admin",
                data=""
            )
        
    @staticmethod
    async def create_admin_service(current_admin: dict, payload: CreateAdmin) -> dict:
        try:
            # Check permission
            if current_admin.get("user_type") != "DEPT_ADMIN":
                return OutModel(
                    status="failure",
                    status_code=403,
                    comment="Access Denied. You dont have permission to create Admins",
                    data=""
                )

            # Check email duplication
            existing_email = await find_one(
                settings.DB_TABLE.ADMINS, {"email": payload.email}
            )
            if existing_email:
                return OutModel(
                    status="failure",
                    status_code=400,
                    comment="Email already exists",
                    data=""
                )

            # Check phone duplication
            existing_phone = await find_one(
                settings.DB_TABLE.ADMINS, {"phone_number": payload.phone_number}
            )

            if existing_phone:
                return OutModel(
                    status="failure",
                    status_code=400,
                    comment="Phone number already exists",
                    data=""
                )
            
            now = int(time.time())
            # Create admin document
            new_admin = Admin(
                uuid=await generate_uuid(),
                firstname=payload.firstname,
                surname=payload.surname,
                email=payload.email,
                country=payload.country,
                country_code=payload.country_code,
                phone_number=payload.phone_number,
                password=await hash_password(payload.password),
                user_type="ADMIN",
                user_roles=payload.user_roles,
                created_by=current_admin["uuid"],
                created_at=now,
                updated_at=now,
            ).model_dump()

            await insert_one(
                settings.DB_TABLE.ADMINS, new_admin
            )

            logger.info(f"Admin created by {current_admin['uuid']}: {new_admin['uuid']}")

            new_admin.pop("_id", None)
            new_admin.pop("password", None)
            return OutModel(
                status="success",
                status_code=201,
                comment="Admin created successfully",
                data=new_admin
            )

        except Exception as e:
            logger.error(f"Failed to create admin: {str(e)}")
            return OutModel(
                status="error",
                status_code=500,
                comment=f"Failed to create admin: {str(e)}",
                data="",
            )
        
    @staticmethod
    async def get_current_user_details(current_user: dict) -> dict:
        try:
            # Fetch from DB to get latest details
            user = await find_one(
                settings.DB_TABLE.ADMINS,
                {"uuid": current_user["uuid"]}
            )

            if not user:
                logger.info(f"User not found: {current_user['uuid']}")
                return OutModel(
                    status="success",
                    status_code=200,
                    comment="User not found",
                    data=""
                )

            feilds_to_remove = ["_id", "created_at", "updated_at", "password"]
            for field in feilds_to_remove:
                user.pop(field, None) 
            
            logger.info(f"Successfully Fetched current user details: {user}")
            return OutModel(
                status="success",
                status_code=200,
                comment="Current user details fetched successfully",
                data=user
            )
        except Exception as e:
            logger.error(f"Failed to fetch current user details: {str(e)}")
            return OutModel(
                status="error",
                status_code=500,
                comment=f"Failed to fetch current user details: {str(e)}",
                data=""
            )
        
    @staticmethod
    async def admin_login(email: str, password: str) -> OutModel:
        try:
            # Find admin by email
            admin = await find_one(
                settings.DB_TABLE.ADMINS,
                {"email": email}
            )

            if not admin:
                logger.info(f"Admin not found for email: {email}")
                return OutModel(
                    status="error",
                    status_code=404,
                    comment="Invalid email or password",
                    data=""
                )

            # Verify password
            if not await verify_password(password, admin["password"]):
                logger.info(f"Invalid credentials for email: {email}")
                return OutModel(
                    status="error",
                    status_code=401,
                    comment="Invalid email or password",
                    data=""
                )

            # Generate JWT
            token_data = {
                "uuid": admin["uuid"],
                "email": admin["email"]
            }

            logger.info(f"Creating JWT for admin: {admin['uuid']} with email: {admin['email']}")

            access_token = await create_access_token(data=token_data)

            logger.info(f"JWT created with email: {admin['email']} : {access_token}")
            return OutModel(
                status="success",
                status_code=200,
                comment="Login successful",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    # "admin_id": admin["uuid"],
                    # "email": admin["email"],
                    # "user_type": admin.get("user_type")
                }
            )

        except Exception as e:
            logger.error(f"Failed to login admin: {str(e)}")
            return OutModel(
                status="error",
                status_code=500,
                comment=f"Failed to login admin: {str(e)}",
                data=""
            )
