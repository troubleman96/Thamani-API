from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    errors: Optional[list[str]] = None
    meta: Optional[dict[str, Any]] = None


def ok(data: T = None, message: str = "OK", meta: dict = None) -> ApiResponse[T]:
    return ApiResponse(success=True, message=message, data=data, meta=meta)


def fail(message: str, errors: list[str] = None, data: T = None) -> ApiResponse[T]:
    return ApiResponse(success=False, message=message, data=data, errors=errors)
