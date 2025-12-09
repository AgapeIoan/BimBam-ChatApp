from app.utils.errors.base_app_exception import BaseAppException
class UserNotFoundException(BaseAppException):
    """Raised when a user is not found"""
    def __init__(self, message: str = "User not found"):
        super().__init__(message, status_code=404)