from typing import Optional
from pydantic import BaseModel, EmailStr

class DemoPostForm(BaseModel):
    """demo模型"""
    name: str
    description: Optional[str] = None
    price: float
    txt: float