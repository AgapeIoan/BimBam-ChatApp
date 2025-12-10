from app.utils.errors.base_app_exception import BaseAppException


class ValidationException(BaseAppException):
    """Raised when input validation fails"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)