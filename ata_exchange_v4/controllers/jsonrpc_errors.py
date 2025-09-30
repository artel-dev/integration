from odoo.exceptions import UserError

from odoo.addons.ata_exchange_v4.models.ata_exchange_method import AtaExchangeMethod
from odoo.addons.ata_exchange_v4.models.ata_exchange_log import ExchangeLog


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
    def __init__(self, message: str, code: int, data=None, log_id: ExchangeLog | None = None):
        super().__init__(message)
        self.code = code
        self.data = data or {}

        if log_id:
            log_id.write({
                'response': message
            }, use_new_cursor=True)

class ApiKeyMissingError(JsonRpcApiError):
    def __init__(self, method: AtaExchangeMethod, **kwargs):
        super().__init__(f"API Key is required for method '{method.name}'.", ERROR_API_KEY_MISSING, **kwargs)

class ApiKeyInvalidError(JsonRpcApiError):
    def __init__(self, method: AtaExchangeMethod, **kwargs):
        super().__init__(f"Invalid or inactive API key for method '{method.name}'.", ERROR_API_KEY_INVALID, **kwargs)

class MethodNotFoundError(JsonRpcApiError):
    def __init__(self, method_name, **kwargs):
        msg = f"Method '{method_name}' (type='incoming_request') not found."
        super().__init__(msg, ERROR_METHOD_NOT_FOUND, **kwargs)

class InvalidJsonError(JsonRpcApiError):
    def __init__(self, method_name, error_parsing: Exception | None = None, **kwargs):
        msg = f"Invalid JSON in request for method '{method_name}': {error_parsing}"
        super().__init__(msg, ERROR_INVALID_JSON, **kwargs)

class ServerError(JsonRpcApiError):
    def __init__(self, message="Server error.", **kwargs):
        super().__init__(message, ERROR_SERVER_ERROR, **kwargs)
