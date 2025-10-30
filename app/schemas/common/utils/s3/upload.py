from pydantic import BaseModel
from typing import Any, Dict, List
from enum import Enum


class FileTypeEnum(str, Enum):
    KYC_DOCS = "KYC_DOCS"
    MEDIAS = "MEDIAS"


class SingleFileUploadResponse(BaseModel):
    filename: str
    file_url: str


class MultiFileUploadResponse(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    successful_urls: List[str]
    file_data: List[Dict[str, Any]]