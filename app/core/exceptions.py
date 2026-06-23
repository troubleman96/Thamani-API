from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.response import ApiResponse


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            success=False,
            message=exc.detail,
            data=None,
            errors=[str(exc.detail)],
        ).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        f"{' -> '.join(str(l) for l in e['loc'])}: {e['msg']}"
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ApiResponse(
            success=False,
            message="Validation failed",
            data=None,
            errors=errors,
        ).model_dump(),
    )
