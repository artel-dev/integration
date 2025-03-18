from odoo import http
from odoo.http import request


class AtaExchangeIncomingController(http.Controller):
    @http.route("/api/ata_exchange_v4", auth='public', type='json', methods=['POST'], cors='*', csrf=False)
    def method_request(self, **kw) -> dict:
        request_data = request.env['ata.exchange.json'].loads(request.httprequest.data)
        
        return request.env['ata.exchange.handler'].process_incoming_request(request_data, request.env)
