from app.utils.errors.base_app_exception import BaseAppException


class DatabaseException(BaseAppException):
    """Raised for general database errors"""
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)