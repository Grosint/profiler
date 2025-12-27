from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class APIError(BaseModel):
    message: str
    code: str
    details: dict | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[APIError] = None
