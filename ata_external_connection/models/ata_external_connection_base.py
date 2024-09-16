from odoo import api, models, fields, Command
from odoo.tools.misc import get_lang
from abc import abstractmethod

from .ata_external_connection_method import AtaExternalConnectionMethod as ExtMethod


class AtaExternalConnectionClass(models.AbstractModel):
    _name = "ata.external.connection.class"
    _description = "External connection class extension"

    ATA_EXCHANGE_NODE_NAME = ""

    ata_exchange_method_ids = fields.Many2many(
        comodel_name="ata.external.connection.method",
        compute="ata_exchange_compute_methods",
    )

    def ata_exchange_compute_methods(self, methods: list[ExtMethod] = []) -> None:
        for record in self:
            record.ata_exchange_method_ids |=\
                self.env['ata.external.connection.method'].browse([m.id for m in methods])

    def ata_exchange_add_to_queue(self):
        for record in self:
            self.env['ata.exchange.queue'].add_to_queue(record)

    def ata_exchange_get_ref_from_record(self) -> str|None:
        self.ensure_one()
        return "%s,%s" % (self._name, self.id) if self else None

    def ata_exchange_get_request_data(self, method: ExtMethod) -> dict:
        return data if (data:=self.ata_exchange_get_data_record(method, True)) else {}

    @abstractmethod
    def ata_exchange_get_data_record(self, method: ExtMethod|None, as_node = False) -> list[dict]|dict|str:
        pass

    def ata_exchange_get_data_record_multi(self, data: list[dict], as_node = False) -> list[dict]|dict|str:
        if len(data) == 0:
            out = ""
        elif len(data) == 1:
            out = data[0]
        else:
            out = data

        if as_node and self.ATA_EXCHANGE_NODE_NAME:
            out = {
                self.ATA_EXCHANGE_NODE_NAME: out
            }

        return out

    @api.model
    def ata_exchange_get_request_body(self, method: ExtMethod, request_data: dict) -> dict:
        return {
            "meta": {},
            "data": request_data,
        }

    @api.model
    def ata_exchange_response_body_parse(self, method: ExtMethod, response_body: dict) -> tuple[dict, bool]:
        # typical parse response
        response_data: dict = response_body.get("data", {})
        result = response_data.get("status", False)

        return response_data, result

    def ata_exchange_response_post_processing(self, method: ExtMethod, response_data: dict) -> bool:
        return True

    @staticmethod
    def _str_empty(value):
        return str(value) if value else ''


class AtaExternalConnectionBase(models.AbstractModel):
    _name = "ata.external.connection.base"
    _description = "External connection base model"

    _inherit = ['ata.external.connection.method.mixing']

    @api.model
    def get_default_lang(self):
        return 'en_US'

    # --- re-exchanged ---
    _re_exchanged = set()

    @api.model
    def _re_exchanged_in(self, record:AtaExternalConnectionClass) -> bool:
        return record.ata_exchange_get_ref_from_record() in self._re_exchanged

    @api.model
    def _re_exchanged_add(self, record:AtaExternalConnectionClass) -> None:
        self._re_exchanged.add(record.ata_exchange_get_ref_from_record())

    @api.model
    def _re_exchanged_delete(self, record:AtaExternalConnectionClass) -> None:
        self._re_exchanged.discard(record.ata_exchange_get_ref_from_record())

    # --- main function exchange ---
    @api.model
    def exchange(self, record:AtaExternalConnectionClass, method: ExtMethod) -> bool:
        # by default the exchange is successful
        result_main = True

        self = self.with_context(lang=self.get_default_lang())

        # сhecking the record for the exchange method at the moment
        # it may be that the record no longer needs to be exchanged
        for method in record.ata_exchange_method_ids:
            ext_systems = self.env["ata.external.connection.domain"].get_ext_systems(record, method)
            for ext_system in ext_systems:
                result = False
                
                request_data = record.ata_exchange_get_request_data(method)
                # request_data may be empty
                if request_data:
                    record_name = record.name if "name" in record.fields_get("name") else ""
                    ext_service = {
                        'exchange_id': f'{record._name} ({record.id}), {record_name}' if record else '',
                        'name': f'{method.description}',
                        'description': f'{method.description}',
                        'method_name': f'{method.name}',
                        'http_method': 'POST',
                        'params': dict(),
                        'request_body': record.ata_exchange_get_request_body(method, request_data)
                    }

                    response_body = ext_system.execute(ext_service)
                    if response_body:
                        error = response_body.get("error", False)
                        if not error:
                            # parse response body
                            response_data, result_response_body_parse = record.ata_exchange_response_body_parse(method, response_body)
                            if result_response_body_parse:
                                # post-processing response data
                                self._re_exchanged_add(record)
                                result = record.ata_exchange_response_post_processing(method, response_data)
                                self._re_exchanged_delete(record)

                result_main = result_main and result
        
        return result_main

    # --- incoming request ---
    @api.model
    def handle_request(self, request_data, method_name: str) -> dict:
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
    def _formation_response(self, method: ExtMethod, result) -> dict:
        func_post_processing_name = f'ata_formation_response_{method.name.lower()}'
        return getattr(self.env[method.model_name], func_post_processing_name)(result) \
            if hasattr(self.env[method.model_name], func_post_processing_name)\
            else self.response_form(result)

    @classmethod
    def response_form(cls, result) -> dict:
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

