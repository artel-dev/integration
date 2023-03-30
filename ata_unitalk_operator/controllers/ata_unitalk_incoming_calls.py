from odoo import http
from odoo.http import request


class UnitalkIncomingCalls(http.Controller):

    @http.route('/incalls', type='http', auth='public', website=True)
    def answer_call(self, **post):
        data_calls = {'calls': 'ns'}
        return request.render('ata_unitalk_operator.tmp_data_history_calls', data_calls)
