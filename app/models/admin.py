# --- app/models/admin_model.py ---
from pydantic import BaseModel, EmailStr
from typing import List, Literal, Optional

class SuperAdmin(BaseModel):
    uuid: str
    firstname: str
    surname: str
    country: str
    email: EmailStr
    country_code: str
    phone_number: str
    password: str
    user_type: str = "SUPER_ADMIN"
    created_at: int
    updated_at: int

class DepartmentAdmin(BaseModel):
    uuid: str
    firstname: str
    surname: str
    country: str
    email: EmailStr
    country_code: str
    phone_number: str
    password: str
    user_type: str = "DEPT_ADMIN"
    created_by: str
    created_at: int
    updated_at: int

class Admin(BaseModel):
    uuid: str
    firstname: str
    surname: str
    country: str
    email: EmailStr
    country_code: str
    phone_number: str
    password: str
    user_type: str = "ADMIN"
    user_roles: List[str]
    created_by: str
    created_at: int
    updated_at: int
