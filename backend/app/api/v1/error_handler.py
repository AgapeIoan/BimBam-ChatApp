import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.utils.errors.base_app_exception import BaseAppException
from app.utils.errors.database_exception import DatabaseException
from app.utils.errors.forbidden_exception import ForbiddenException
from app.utils.errors.resource_not_found import ResourceNotFoundException
from app.utils.errors.unauthorized_exception import UnauthorizedException
from app.utils.errors.user_not_found_exception import UserNotFoundException
from app.utils.errors.validation_exception import ValidationException


def register_error_handlers(app):
    @app.exception_handler(BaseAppException)
    async def handle_app_error(request: Request, exc: BaseAppException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.message})

    @app.exception_handler(DatabaseException)
    async def handle_database_error(request: Request, exc: DatabaseException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "A database error occurred."},
        )

    @app.exception_handler(UnauthorizedException)
    async def handle_unauthorized_error(request: Request, exc: UnauthorizedException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"error": exc.message}
        )

    @app.exception_handler(ResourceNotFoundException)
    async def handle_not_found_error(request: Request, exc: ResourceNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"error": exc.message}
        )

    @app.exception_handler(ValidationException)
    async def handle_validation_error(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"error": exc.message}
        )

    @app.exception_handler(UserNotFoundException)
    async def handle_user_not_found_error(request: Request, exc: UserNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"error": exc.message}
        )

    @app.exception_handler(ForbiddenException)
    async def handle_forbidden_error(request: Request, exc: ForbiddenException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"error": exc.message}
        )

    @app.exception_handler(Exception)
    async def handle_generic_error(request: Request, exc: Exception):
        print(
            "\n--- INTERNAL SERVER ERROR ---\n",
            traceback.format_exc(),
            "\n----------------------------\n",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Internal server error: {str(exc)}"},
        )
