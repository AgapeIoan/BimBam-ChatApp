from app.utils.errors.base_app_exception import BaseAppException


class ServiceUnavailableException(BaseAppException):
    """
    Raised when an external dependency (e.g., OpenAI) is not configured or unavailable.
    """

    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message=message, status_code=503)
