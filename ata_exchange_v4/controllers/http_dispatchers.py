import collections.abc

from odoo.http import JsonRPCDispatcher
from .jsonrpc_errors import JsonRpcApiError

class AtaJsonRPCDispatcher(JsonRPCDispatcher):
    routing_type = 'ata_json'

    def handle_error(self, exc: Exception) -> collections.abc.Callable:
        """
        Overrides the default error handler to remove debug info for specific exceptions.
        """
        if isinstance(exc, JsonRpcApiError):
            error = {
                'code': exc.code,
                'message': str(exc),
                'data': exc.data,
            }
            return self._response(error=error)
        else:
            return super().handle_error(exc)
