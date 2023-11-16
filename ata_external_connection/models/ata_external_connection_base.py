from odoo import api, models
from typing import Tuple


# predefined function in modules:
# ata_get_data_exchange_{method.lower()}() - get dict() data for send to ext. system for (model, method)
# ata_get_data_exchange_1c() - get dict() data for subordinates objects
# ata_request_body_exchange_{method.lower()}() - request body customization
# ata_parse_response_exchange_{method.lower()} - parsing response body
# ata_post_processing_exchange_{method.lower()} - processing after receipt response


class AtaExternalConnectionBase(models.AbstractModel):
    _name = "ata.external.connection.base"
    _description = "External connection base model"

    _inherit = ['ata.external.connection.method.mixing']

    @api.model
    def start_exchange(self, record, method, immediately=False):
        model_id = record._name
        if self.need_exchange(model_id):
            # checking the need to add for exchange queue
            if immediately is False and self.env["ata.exchange.queue.usage"].use_exchange_queue(model_id):
                self.add_exchange_queue(record, method)
            else:
                self.exchange(record, method)

    @api.model
    def need_exchange(self, model_id):
        # checking the need for an exchange on the basis of a one-time exchange
        return True

    @api.model
    def add_exchange_queue(self, record, method):
        self.env["ata.exchange.queue"].add(record, method)

    @api.model
    def exchange(self, record, method):
        result = False

        ext_systems = self.env["ata.external.connection.domain"].get_ext_systems(record, method)
        for ext_system in ext_systems:
            request_data = self._get_request_data(record, method)
            # request_data may be empty
            if request_data:
                ext_service = {
                    'exchange_id': f'Model: {record._name}, Id: {record.id}',
                    'name': f'/{method}',
                    'description': f'/{method}',
                    'method_name': f'{method}',
                    'http_method': 'POST',
                    'params': dict(),
                    'request_body': self._get_request_body(record, method, request_data)
                }

                response_body = ext_system.execute(ext_service)
                if response_body:
                    error = response_body.get("Error", False)
                    if not error:
                        # parse response body
                        response_data, result = self._parse_response_body(record, method, response_body)
                        # post-processing response data
                        result = result and self._post_processing_request(record, method, response_data)

        return result

    @staticmethod
    def _get_request_data(record, method: str) -> dict:
        func_get_data_name = f'ata_get_data_exchange_{method.lower()}'
        return getattr(record, func_get_data_name)() \
            if hasattr(record, func_get_data_name) \
            else {}

    @staticmethod
    def _get_request_body(record, method: str, request_data: dict) -> dict:
        func_request_body_name = f'ata_request_body_exchange_{method.lower()}'
        return getattr(record, func_request_body_name)(request_data) \
            if hasattr(record, func_request_body_name) \
            else {"Data": request_data}

    @staticmethod
    def _parse_response_body(record, method: str, response_body: dict) -> Tuple[dict, bool]:
        func_parse_response_name = f'ata_parse_response_exchange_{method.lower()}'
        if hasattr(record, func_parse_response_name):
            response_data, result = getattr(record, func_parse_response_name)(response_body)
        else:
            # typical parse response
            response_data = response_body.get("Data", {})
            result = response_data.get("Status", False)

        return response_data, result

    @staticmethod
    def _post_processing_request(record, method: str, response_data: dict) -> bool:
        func_post_processing_name = f'ata_post_processing_exchange_{method.lower()}'
        return getattr(record, func_post_processing_name)(response_data) \
            if hasattr(record, func_post_processing_name) else False

    @api.model
    def get_record_data_exchange(self, record, type_exchange=""):
        if record and type_exchange:
            func_get_data_name = f'ata_get_data_exchange_{type_exchange}'
            return getattr(record, func_get_data_name)() if hasattr(record, func_get_data_name) else {}
        else:
            return {}

    @api.model
    def get_record_data_exchange_1c(self, record):
        return self.get_record_data_exchange(record, "1c")
