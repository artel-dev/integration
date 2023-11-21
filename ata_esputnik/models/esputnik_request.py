from typing import List

import logging
import requests
import json

from odoo import fields, models


_logger = logging.getLogger(__name__)


class EsputnikRequest(models.TransientModel):
    """
    Model for making requests to the eSputnik API.

    Allows sending events to eSputnik by calling the post_event() method.

    Attributes:
        base_url (str): The base URL for the eSputnik API
        headers (dict): The headers to send with each API request
        user (str): Name used with the API token
        token (str): The API token used for authentication
    """
    _name = 'esputnik.request'
    _description = 'eSputnik Request'

    base_url = 'https://esputnik.com/api/v2'
    headers = {'Content-Type': 'application/json'}

    user = fields.Char(required=True)
    token = fields.Char(required=True)

    def _post(self, url: str, body: str) -> requests.Response:
        ''' Execute a POST request to the eSputnik API. '''
        return requests.request(
            "POST", url, headers=self.headers, data=body,
            auth=(self.user, self.token)
        )

    def post_event(self, event_name: str,
                   key_value: str, params: List[dict]) -> bool:
        '''
        Create an event in eSputnik.

        Parameters:
        - event_name (str): Name of the event to create
        - key_value (str): Key value to associate with the event
        - params (List[dict]): List of dictionaries to pass with the event.
          Each dict must have a 'name' and 'value' entry.

        Returns:
        - bool: True if the event was created successfully, False otherwise.
        '''
        path = '/event'
        url = self.base_url + path
        payload = json.dumps({
            "eventTypeKey": event_name,
            "keyValue": key_value,
            "params": params,
        })
        response = self._post(url, payload)
        _logger.info('notification sent for %s', key_value)
        return response.status_code == 200
