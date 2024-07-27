from odoo import api, models
from typing import Tuple
from odoo.tools.misc import get_lang

from .ata_external_connection_method import AtaExternalConnectionMethod as ExtMethod


# predefined function in modules:
# ata_prepare_exchange_{method.lower()}() - prepare record after exchange.
#   return continue_exchange, delete_from_queue
# ata_get_data_exchange_{method.lower()}() - get dict() data for send to ext. system for (model, method)
# ata_get_data_exchange_1c() - get dict() data for subordinates objects
# ata_request_body_exchange_{method.lower()}() - request body customization
# ata_parse_response_exchange_{method.lower()} - parsing response body
# ata_post_processing_exchange_{method.lower()} - processing after receipt response


class AtaExternalConnectionBase(models.AbstractModel):
    _name = "ata.external.connection.base"
    _description = "External connection base model"

    _inherit = ['ata.external.connection.method.mixing']

    _re_exchanged = []

    @api.model
    def get_default_lang(self):
        return 'en_US'

    # --- outgoing exchange ---
    @api.model
    def start_exchange(self, record, method_name: str, immediately=False) -> bool:
        if isinstance(record.id, models.NewId):
            return False

        method = self._get_method_for_name(method_name)
        if method and self.need_exchange(method) and not self._record_in_re_exchanged(record):
            # checking the need to add for exchange queue
            if immediately is False and self.env["ata.exchange.queue.usage"].use_exchange_queue(method):
                if self._prepare_record(record, method)[0]:
                    self.add_exchange_queue(record, method)
            else:
                self.exchange(record, method)

    # check for recursive re-exchange
    @api.model
    def _record_in_re_exchanged(self, record) -> bool:
        ref = self._get_ref_from_record(record)
        return ref in self._re_exchanged

    @api.model
    def _add_re_exchanged(self, record) -> None:
        ref = self._get_ref_from_record(record)
        self._re_exchanged.append(ref)

    @api.model
    def _delete_re_exchanged(self, record) -> None:
        ref = self._get_ref_from_record(record)
        if ref in self._re_exchanged:
            self._re_exchanged.remove(ref)

    @api.model
    def need_exchange(self, method: ExtMethod):
        # checking the need for an exchange on the basis of a one-time exchange
        return True

    @api.model
    def add_exchange_queue(self, record, method: ExtMethod):
        self.env["ata.exchange.queue"].add(record, method)

    @api.model
    def exchange(self, record, method: ExtMethod) -> bool:
        result = False
        self = self.with_context(lang=self.get_default_lang())

        self._add_re_exchanged(record)

        ext_systems = self.env["ata.external.connection.domain"].get_ext_systems(record, method)
        if ext_systems:
            # prepare record after exchange
            continue_exchange, delete_from_queue = self._prepare_record(record, method)
            if continue_exchange:
                for ext_system in ext_systems:
                    request_data = self._get_request_data(record, method)
                    # request_data may be empty
                    if request_data:
                        ext_service = {
                            'exchange_id': f'Model: {record._name}, Id: {record.id}' if record else '',
                            'name': f'{method.description}',
                            'description': f'{method.description}',
                            'method_name': f'{method.name}',
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
                                result = result and self._post_processing_response(record, method, response_data)
                    else:
                        # for delete from queue
                        result = True
            elif delete_from_queue:
                result = True
        else:
            # for delete from queue, if nothing ext. systems
            result = True

        self._delete_re_exchanged(record)

        return result

    @staticmethod
    # return [continue_exchange, delete_from_queue]
    def _prepare_record(record, method: ExtMethod) -> Tuple[bool, bool]:
        func_prepare_name = f'ata_prepare_exchange_{method.name.lower()}'
        return getattr(record, func_prepare_name)() \
            if hasattr(record, func_prepare_name)\
            else (True, False)

    @api.model
    def _get_request_data(self, record, method: ExtMethod) -> dict:
        func_get_data_name = f'ata_get_data_exchange_{method.name.lower()}'
        record_model = record.with_context(lang=self.env.lang) \
            if record \
            else self.env[method.model_name].with_context(lang=self.env.lang)

        return getattr(record_model, func_get_data_name)() \
            if hasattr(record_model, func_get_data_name) \
            else {}

    @staticmethod
    def _get_request_body(record, method: ExtMethod, request_data: dict) -> dict:
        func_request_body_name = f'ata_request_body_exchange_{method.name.lower()}'
        return getattr(record, func_request_body_name)(request_data) \
            if hasattr(record, func_request_body_name) \
            else {"Data": request_data}

    @staticmethod
    def _parse_response_body(record, method: ExtMethod, response_body: dict) -> Tuple[dict, bool]:
        func_parse_response_name = f'ata_parse_response_exchange_{method.name.lower()}'
        if hasattr(record, func_parse_response_name):
            response_data, result = getattr(record, func_parse_response_name)(response_body)
        else:
            # typical parse response
            response_data = response_body.get("Data", {})
            result = response_data.get("Status", False)

        return response_data, result

    @staticmethod
    def _post_processing_response(record, method: ExtMethod, response_data: dict) -> bool:
        func_post_processing_name = f'ata_post_processing_exchange_{method.name.lower()}'
        return getattr(record, func_post_processing_name)(response_data) \
            if hasattr(record, func_post_processing_name) else True

    @staticmethod
    def get_record_data_exchange(record, type_exchange: str = "", **kwargs) -> dict:
        if record and type_exchange:
            func_get_data_name = f'ata_get_data_exchange_{type_exchange}'
            return getattr(record, func_get_data_name)(**kwargs) if hasattr(record, func_get_data_name) else {}
        else:
            return {}

    @api.model
    def get_record_data_exchange_1c(self, record, **kwargs) -> dict:
        return self.get_record_data_exchange(record, "1c", **kwargs)

    # --- incoming request ---
    @api.model
    def handle_request(self, request_data, method_name: str):
        method = self._get_method_for_name(method_name)
        if method:
            result = self._handle_request_data_model(request_data, method)
            response_str = self._formation_response(method, result)
        else:
            result = "Processing method not found"
            response_str = self.response_form(result)

        return response_str # self.env['ata.external.connection.json'].dumps(response_str)

    @api.model
    def _handle_request_data_model(self, request_data, method):
        func_post_processing_name = f'ata_handle_request_{method.name.lower()}'
        return getattr(self.env[method.model_name], func_post_processing_name)(request_data) \
            if hasattr(self.env[method.model_name], func_post_processing_name) \
            else False

    @api.model
    def _formation_response(self, method: ExtMethod, result) -> str:
        func_post_processing_name = f'ata_formation_response_{method.name.lower()}'
        return getattr(self.env[method.model_name], func_post_processing_name)(result) \
            if hasattr(self.env[method.model_name], func_post_processing_name)\
            else self.response_form(result)

    @classmethod
    def response_form(cls, result):
        if isinstance(result, dict) or isinstance(result, str):
            _response = {"Error": result}
        elif result:
            _response = {"Data": {"Status": True}}
        else:
            _response = {"Data": {"Status": False}}

        return _response

    # --- additional functions ---
    @api.model
    def save_attachment(self, save_data: dict) -> None:
        attachments_items = self.env["ir.attachment"].sudo().search(
            [("res_id", "=", save_data["record_id"]),
            ('res_model', '=', save_data["model_name"]),
            ('name', '=', save_data["file_name"])])

        if attachments_items:
            attachment = attachments_items[0]
            vals = {
                'datas': save_data["file_data"]
            }
            attachment.write(vals)
        else:
            self.env['ir.attachment'].sudo().create({
                'name': save_data["file_name"],
                'type': 'binary',
                'res_id': save_data["record_id"],
                'res_model': save_data["model_name"],
                'datas': save_data["file_data"],
                'mimetype': save_data["mimetype"]
            })
