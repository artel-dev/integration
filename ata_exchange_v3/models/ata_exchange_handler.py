from odoo import models, fields, api
from abc import abstractmethod

from odoo.addons.ata_exchange_v3.models.ata_exchange_system import AtaExchangeSystem as ExSystem
from odoo.addons.ata_exchange_v3.models.ata_exchange_method import AtaExchangeMethod as ExMethod


class AtaExchangeHandler(models.Model):
    _name = "ata.exchange.handler"
    _description = "Model for handling incoming requests"

    method_id = fields.Many2one(
        comodel_name='ata.exchange.method')
    type_request = fields.Selection(
        selection=[
            ('incoming', 'Incoming request'),
            ('outgoing', 'Outgoing request')
        ])
    ext_system_id = fields.Many2one(
        comodel_name='ata.exchange.system',
        # compute="compute_fields",
        store=False)
    request_data = fields.Json(
        store=False,)

    @classmethod
    def process_incoming_request(cls, request_data: dict, env):
        def check_request_meta():
            if (meta := request_data.get('meta','')) and isinstance(meta, dict):
                # check for database
                # можливо ще не було синхронизації або це не наша база
                if (target_db_name := meta.get('odoo_db_name','')) and isinstance(target_db_name, str):
                    if not target_db_name == env.cr.dbname:
                        raise ValueError(f"the database specified in the request '{target_db_name}' does not match the current database")
                else:
                    raise ValueError("error searching, filling or typing 'odoo_db_name' in 'meta' tag in request")
                
                # перевірка id зовнішньої системи odoo, отриманий після синхронізації баз
                if (id_ext_system := meta.get('odoo_id_external_system','')) and isinstance(id_ext_system, int):
                    if env['ata.exchange.system'].sudo().search_count([('id', '=', id_ext_system)]) == 0:
                        raise ValueError(f"the ID external system '{id_ext_system}' specified in the request not matched")
                else:
                    raise ValueError("error searching, filling or typing 'odoo_id_external_system' in 'meta' tag in request")

                # перевірка наявності методу обміну
                if (method_name := meta.get('odoo_method_name','')) and isinstance(method_name, str):
                    if env['ata.exchange.method'].sudo().search_count([('name', '=', method_name)]) == 0:
                        raise ValueError(f"the method name '{method_name}' specified in the request not found")
                else:
                    raise ValueError("error searching, filling or typing 'odoo_method_name' in 'meta' tag in request")
            else:
                raise ValueError("error searching, filling or typing 'meta' tag in request")

        def get_response_body_meta() -> dict:
            return {
                'meta': {
                    'odoo_db_name': env.cr.dbname,
                },
            }

        def get_response_body_error(error) -> dict:
            return {
                **get_response_body_meta(),
                **{'error': error}
            }

        def get_response_body_data(data: dict) -> dict:
            # додатково передаємо статус для підтверждення успішного виконання
            # він може перекритися негативним статусом з data
            status = data.pop('status') if 'status' in data else True
            return {
                **get_response_body_meta(),
                **{'status': status},
                **{'data': data}
            }

        def get_ext_system() -> ExSystem:
            _meta: dict = request_data.get('meta', False)
            _id_ext_system =_meta.get('odoo_id_external_system', False) if _meta else False
            return env['ata.exchange.system'].sudo().search([('id', '=', _id_ext_system)], limit=1)

        def get_method() -> ExMethod:
            _meta: dict = request_data.get('meta', False)
            _name_method =_meta.get('odoo_method_name', False) if _meta else False
            if not (method := env['ata.exchange.method'].sudo().search([('name', '=', _name_method)], limit=1)):
                raise ValueError(f"Method name '{_name_method}' not found")

            return method

        # перевіряємо на коректність вхідних даних meta        
        try:
            check_request_meta()            
        except ValueError as e:
            return get_response_body_error(str(e))

        handler_id = env['ata.exchange.handler'].sudo().search([
            ('type_request', '=', 'incoming'),
            ('method_id.name', '=', get_method().name)
        ], limit=1)
        func_name = f'process_request_incoming_{get_method().name}'
        if handler_id:
            if hasattr(handler_id,func_name):
                try:
                    handler_id.request_data = request_data.get('data', [])
                    handler_id.ext_system_id = get_ext_system().id
                    result = getattr(handler_id,func_name)()
                    return get_response_body_data(result)
                except ValueError as e:
                    return get_response_body_error(str(e))
            else:
                return get_response_body_error(f"Function of handler for method '{get_method().name}' not found")
        else:
            return get_response_body_error(f"Incoming request handler for method '{get_method().name}' not found")
