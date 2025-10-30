from pydantic import BaseModel
from typing import Optional,Any


class OutModel(BaseModel):
    status: str
    status_code: int
    comment: Optional[str]
    data: Any