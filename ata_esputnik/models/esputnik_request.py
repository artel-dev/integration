from typing import List

import logging
import requests
import json

from odoo import fields, models


_logger = logging.getLogger(__name__)


# TODO: documentation
class EsputnikRequest(models.TransientModel):
    _name = 'esputnik.request'
    _description = 'eSputnik Request'

    base_url = 'https://esputnik.com/api/v2'
    headers = {'Content-Type': 'application/json'}

    user = fields.Char(required=True)
    token = fields.Char(required=True)

    def _post(self, url: str, data: str) -> requests.Response:
        return requests.request(
            "POST", url, headers=self.headers, data=data,
            auth=(self.user, self.token)
        )

    # TODO: documentation
    def post_event(self, event_name: str, key_value: str, params: List) -> bool:
        path = '/event'
        url = self.base_url + path
        payload = json.dumps({
            "eventTypeKey": event_name,
            "keyValue": key_value,
            "params": params,
        })
        response = self._post(url, payload)
        _logger.warning('notification sent for %s', key_value)
        return response.status_code == 200
