from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from app.db.mongo.mongodb import find_one
from app.models.base import OutModel
from app.core.security import create_access_token, decode_jwt_token, get_current_admin
from app.schemas.admin import AdminLoginRequest, CreateAdmin, CreateDepartmentAdmin, CreateSuperAdmin
from app.services.auth.auth_service import AuthService
from pydantic import EmailStr
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/create-super-admin", response_model=OutModel)
async def create_super_admin(
    payload: CreateSuperAdmin,
    secret_key: str = Query(..., description="Secret key for Super Admin creation"),
):
    """
    Create a Super Admin.
    """
    try:
        result = await AuthService.create_super_admin(payload, secret_key)
        return result
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to create super admin",
            data=str(e),
        )

@router.post("/create-dept-admin", response_model=OutModel)
async def create_deptartment_admin(
    payload: CreateDepartmentAdmin,
    current_admin=Depends(get_current_admin)
):
    """
    Create a Department Admin.
    """
    try:
        return await AuthService.create_department_admin(payload, current_admin)

    except Exception as e:        
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to create department admin",
            data=str(e),
        )
    
@router.post("/create-admin", response_model=OutModel)
async def create_admin(
    payload: CreateAdmin,
    current_admin: dict = Depends(get_current_admin),
):
    try:
        return await AuthService.create_admin_service(current_admin, payload)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to create admin",
            data=str(e),
        )
    
@router.get("/me", response_model=OutModel)
async def get_current_admin_profile(current_admin: dict = Depends(get_current_admin)):
    try:
        return await AuthService.get_current_user_details(current_admin)
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to get current admin profile",
            data=str(e),
        )
    
@router.post("/login", response_model=OutModel)
async def admin_login(payload: AdminLoginRequest):
    try:
        return await AuthService.admin_login(
            email=payload.email, password=payload.password
        )
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Internal server error",
            data="",
        )