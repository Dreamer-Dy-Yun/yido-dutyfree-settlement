from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class CustomException(Exception):
    """커스텀 예외 기본 클래스"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class NotFoundError(CustomException):
    """리소스를 찾을 수 없을 때"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=404, message=message)


class UnauthorizedError(CustomException):
    """인증이 필요할 때"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status_code=401, message=message)


class ForbiddenError(CustomException):
    """권한이 없을 때"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(status_code=403, message=message)


class BadRequestError(CustomException):
    """잘못된 요청일 때"""
    def __init__(self, message: str = "Bad request"):
        super().__init__(status_code=400, message=message)


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 설정"""
    
    @app.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()}
        )
