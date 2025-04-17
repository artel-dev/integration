from odoo.exceptions import UserError

from odoo.addons.ata_exchange_v4.models.ata_exchange_method import AtaExchangeMethod

# JSON-RPC error codes
ERROR_API_KEY_MISSING = -32001
ERROR_API_KEY_INVALID = -32002
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_JSON = -32700
ERROR_SERVER_ERROR = -32603


class JsonRpcApiError(UserError):
    """
    Base exception for JSON-RPC errors.
    """
    def __init__(self, message: str, code: int, data=None):
        super().__init__(message)
        self.code = code
        self.data = data or {}

class ApiKeyMissingError(JsonRpcApiError):
    def __init__(self, method: AtaExchangeMethod, data=None):
        super().__init__(f"API Key is required for method '{method.name}'.", ERROR_API_KEY_MISSING, data)

class ApiKeyInvalidError(JsonRpcApiError):
    def __init__(self, method: AtaExchangeMethod, data=None):
        super().__init__(f"Invalid or inactive API key for method '{method.name}'.", ERROR_API_KEY_INVALID, data)

class MethodNotFoundError(JsonRpcApiError):
    def __init__(self, method_name, data=None):
        msg = f"Method '{method_name}' (type='incoming_request') not found."
        super().__init__(msg, ERROR_METHOD_NOT_FOUND, data)

class InvalidJsonError(JsonRpcApiError):
    def __init__(self, method_name, error_parsing: Exception|None = None, data=None):
        msg = f"Invalid JSON in request for method '{method_name}': {error_parsing}"
        super().__init__(msg, ERROR_INVALID_JSON, data)

class ServerError(JsonRpcApiError):
    def __init__(self, message="Server error.", data=None):
        super().__init__(message, ERROR_SERVER_ERROR, data)
