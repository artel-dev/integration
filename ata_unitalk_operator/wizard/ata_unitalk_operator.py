# -*- coding: utf-8 -*-
import json
import time
from odoo import http
from odoo.http import request
import requests

from odoo import api, fields, models


class UnitalkOperator(models.TransientModel):
    _name = 'ata.unitalk.operator'
    _description = 'Unitalk Operator'
    # _rec_name = 'user_id'

    phone_number = fields.Char(
        string='Phone number:',
    )

    def __init__(self, *args, **kwargs):
        super(UnitalkOperator, self).__init__(*args, **kwargs)
        answ = self.env.context.get('answ')
        # your initialization code here
        if answ:
            self.render_json()

    def start_call(self, tz=False):
        form_data = {
            'number': self.phone_number,
            'meta': 'test',
            'sip': '5229'
        }
        # data = json.dumps(data)
        headers = {'Authorization': 'fYJiWAbeQ70X'}
        base_url = 'https://cstat.nextel.com.ua:8443/tracking/api'
        url = '{}/phones/directCall'.format(base_url)
        r = requests.post(url, form_data, headers=headers)
        answ = json.loads(r.content)
        if answ.get('result', False):
            result = json.loads(answ['result'])
            phonecall_id = result.get('phonecall_id', False)
        # self.appoinment_id.state = 'cancel'
        return {
            'view_mode': 'form',
            'res_model': 'ata.unitalk.operator',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def get_history(self):
        form_data = {
            "dateFrom": "2023-01-01 00:00:00",
            "dateTo": "2023-07-01 00:00:00",
            "limit": 246,
            "offset": 0,
            "filter": {
            }
        }
        form_data = json.dumps(form_data)
        headers = {'Authorization': 'fYJiWAbeQ70X', 'Content-Type': 'application/json'}
        base_url = 'https://cstat.nextel.com.ua:8443/tracking/api'
        url = '{}/history/get'.format(base_url)
        r = requests.post(url, form_data, headers=headers)
        answ = json.loads(r.content)
        if answ.get('count', 0):
            data_history_calls = answ
            # request.render('ata_unitalk_operator.tmp_data_history_calls', data_history_calls)
            context = self.env.context.copy()
            context.update({
                'answ': answ,
                'default_res_id': self.id,
                'default_res_model': 'ata.unitalk.operator',
            })
        return {
            'view_mode': 'form',
            'res_model': 'ata.unitalk.operator',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }

    def render_json(self):
        answ = self.env.context.get('answ')
        # your code to parse the JSON and format it for display in the template
        # ...
        # data = {
        #     'json_data': formatted_json_data,
        # }
        return request.render('ata_unitalk_operator.tmp_data_history_calls', answ)
