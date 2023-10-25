from odoo import api, fields, models


# predefined function in modules:
# ata_get_data_exchange_{method.lower()}() - get dict() data for send to ext. system for (model, method)
# ata_get_data_exchange_1c() - get dict() data for subordinates objects


class AtaExternalConnectionBase(models.AbstractModel):
    _name = "ata.external.connection.base"
    _description = "External connection base model"

    _inherit = ['ata.external.connection.method.mixing']

    @api.model
    def start_exchange(self, record, method):
        model_id = record._name
        if self.need_exchange(model_id):
            # checking the need to add for exchange queue
            if self.env["ata.exchange.queue.usage"].use_exchange_queue(model_id):
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
        result = True
        model_name = record._name

        ext_systems = self.env["ata.external.connection.domain"].get_ext_systems(record, method)
        for ext_system in ext_systems:
            exchange_id = f'Model: {model_name}, Id: {record.id}'

            func_get_data_name = f'ata_get_data_exchange_{method.lower()}'
            if hasattr(record, func_get_data_name):
                ext_service = {
                    'exchange_id': exchange_id,
                    'name': f'/{method}',
                    'description': f'/{method}',
                    'method_name': f'/{method}',
                    'http_method': 'POST',
                    'params': dict(),
                    'request_body': {
                        "Data": getattr(record, func_get_data_name)()
                    }
                }

                response_body = ext_system.execute(ext_service)

                if response_body:
                    error = response_body.get("Error")
                    if not error:
                        data = response_body.get("Data", {})
                        result = min(result, data.get("Status", False))
                    else:
                        result = False
                else:
                    result = False
            else:
                result = False

        return result

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
