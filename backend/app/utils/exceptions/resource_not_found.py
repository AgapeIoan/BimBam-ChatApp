from app.utils.errors.BaseAppException import BaseAppException
class ResourceNotFoundException(BaseAppException):
    """Raised when a requested resource is not found"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)