from app.utils.errors.base_app_exception import BaseAppException


class ForbiddenException(BaseAppException):
    """Raised when user is authenticated but not allowed to perform the action"""

    def __init__(
        self, message: str = "You do not have permission to access this resource"
    ):
        super().__init__(message, status_code=403)