# app/models/user_model.py
from pydantic import BaseModel, EmailStr
from typing import Dict, Optional, Literal


class DocumentFile(BaseModel):
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    front: Optional[str] = None
    back: Optional[str] = None


class UserKycDocuments(BaseModel):
    documents: Dict[str, DocumentFile] = {}


class User(BaseModel):
    uuid: str
    email: EmailStr
    phone_number: str
    country: str
    country_code: str
    full_name: str = ""
    date_of_birth: Optional[str] = None
    nationality: str = ""
    country_of_residence: str = ""
    country_of_birth: str = ""
    full_address: str = ""
    user_type: Literal["ADMIN", "USER"] = "USER"
    status: Literal["ACTIVE", "INACTIVE", "DELETED"] = "ACTIVE"
    otp: int = 0
    kyc_documents: Optional[UserKycDocuments] = None
    metadata: Optional[dict] = None
    created_at: int = 0
    updated_at: int = 0
