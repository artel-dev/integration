from odoo import api, models, fields, Command
from abc import abstractmethod
from typing import Tuple, List, Union, Dict
from functools import wraps
from datetime import date, datetime

from .ata_exchange_method import AtaExchangeMethod as ExMethod


class AtaExchangeClass(models.AbstractModel):
    _name = "ata.exchange.class"
    _description = "Exchange class extension"

    ATA_EXCHANGE_NODE_NAME = ""

    # region [enqueue event] fold
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if records and self.ATA_EXCHANGE_NODE_NAME:
            records.ata_exchange_add_to_queue()
        return records

    def write(self, vals):
        over_write = super().write(vals)
        if over_write and self.ATA_EXCHANGE_NODE_NAME:
            self.ata_exchange_add_to_queue()
        return over_write

    def ata_exchange_add_to_queue(self):
        for record in self:
            self.env['ata.exchange.queue'].add_to_queue(record)
    # endregion

    def ata_exchange_compute_methods(self) -> List[ExMethod]:
        return []
    
    def ata_exchange_get_ref_from_record(self) -> Union[str, None]:
        self.ensure_one()
        return "%s,%s" % (self._name, self.id) if self else None

    def ata_exchange_get_request_data(self, method: ExMethod) -> Union[List[Dict], Dict, str]:
        # as_node - якщо запитуємо дані для кореневої ноди, то в залежності від статусу об'єкта
        # пакет даних може бути пустим. Це робиться для зменшення розміру пакетів обміну
        return data if (data:=self.ata_exchange_get_data_record(method = method, as_node = True)) else {}

    @abstractmethod
    def ata_exchange_get_data_record(self, method: ExMethod, as_node = False) -> Union[List[Dict], Dict, str]:
        pass

    @staticmethod
    def ata_exchange_get_data_record_format(always_list=False):
        def decorator(func):
            @wraps(func)
            def wrapper(self: AtaExchangeClass, *args, **kwargs):
                data = func(self, *args, **kwargs)
                if always_list:
                    out = data
                else:
                    if len(data) == 0:
                        out = ""
                    elif len(data) == 1:
                        out = data[0]
                    else:
                        out = data

                # if kwargs.get('as_node', False) and self.ATA_EXCHANGE_NODE_NAME:
                #     out = {
                #         self.ATA_EXCHANGE_NODE_NAME: out
                #     }

                return out
            return wrapper
        return decorator

    @api.model
    def ata_exchange_get_request_body(self, method: ExMethod, request_data: Union[List[Dict], Dict, str]) -> Dict:
        return {
            **self.get_response_body_meta(),
            "data": request_data,
        }

    @api.model
    def get_response_body_meta(self) -> dict:
        return {
            'meta': {
                'db_name': self._cr.dbname,
            },
        }

    @api.model
    def ata_exchange_response_body_parse(self, method: ExMethod, response_body: dict) -> Tuple[Dict, bool]:
        # typical parse response
        response_data: dict = response_body.get("data", {})
        result = response_body.get("status", False)

        return response_data, result

    def ata_exchange_response_post_processing(self, method: ExMethod, response_data: dict) -> bool:
        return True

    def ata_exchange_get_name(self) -> str:
        return f'{self._name} ({self.id}), {"name" in self._fields and self["name"]}' \
            if isinstance(self, models.Model) else ''

    @staticmethod
    def _str_empty(value):
        if value:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, date):
                return value.strftime("%Y-%m-%d 00:00:00")
            else:
                return str(value)
        else:
            return ''


class AtaExchangeBase(models.AbstractModel):
    _name = "ata.exchange.base"
    _description = "Exchange base model"

    _inherit = ['ata.exchange.method.mixing']

    @api.model
    def get_default_lang(self):
        return 'en_US'

    # region [re-exchanged] fold
    _re_exchanged = set()

    @api.model
    def _re_exchanged_in(self, record:AtaExchangeClass) -> bool:
        return record.ata_exchange_get_ref_from_record() in self._re_exchanged

    @api.model
    def _re_exchanged_add(self, record:AtaExchangeClass) -> None:
        if (ref := record.ata_exchange_get_ref_from_record()):
            self._re_exchanged.add(ref)

    @api.model
    def _re_exchanged_delete(self, record:AtaExchangeClass) -> None:
        if (ref := record.ata_exchange_get_ref_from_record()):
            self._re_exchanged.discard(ref)
    # endregion

    @api.model
    def exchange(self, record:AtaExchangeClass, method: ExMethod) -> bool:
        # by default the exchange is successful
        result_main = True

        self = self.with_context(lang=self.get_default_lang())

        # сhecking the record for the exchange method at the moment
        # it may be that the record no longer needs to be exchanged
        for method in record.ata_exchange_compute_methods():
            ext_systems = self.env["ata.exchange.domain"].get_ext_systems(record, method)
            for ext_system in ext_systems:
                result = False
                
                request_data = record.ata_exchange_get_request_data(method)
                # request_data may be empty
                if request_data:
                    ext_service = {
                        'exchange_id': record.ata_exchange_get_name(),
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
