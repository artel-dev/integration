from odoo import api, models, fields, Command

from abc import abstractmethod
from typing import Tuple, List, Union, Dict, cast
from functools import wraps
from datetime import date, datetime
import logging

from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import ExtResponse
from odoo.addons.mail.models.mail_thread import MailThread

_logger = logging.getLogger(__name__)


class AtaExchangeClass(models.AbstractModel):
    _name = "ata.exchange.class"
    _description = "Exchange class extension"

    _inherit = ['ata.exchange.mixin']

    # потрібно для визначення чи модель потрібно направляти на додавання в чергу або обмін
    # також використувується для формування структури пакету даних
    ATA_EXCHANGE_NODE_NAME = ""

    # region enqueue event
    @api.model_create_multi
    def create(self, vals_list):
        records = self.env[self._name]
        for vals in vals_list:
            record = super().create(vals)
            records |= record
            if record.ata_exchange_check_add_to_queue(vals):
                record.ata_exchange_add_to_queue()

        return records

    def write(self, vals):
        over_write = super().write(vals)
        for record in self:
            if record.ata_exchange_check_add_to_queue(vals):
                record.ata_exchange_add_to_queue()
        return over_write

    def ata_exchange_check_add_to_queue(self, vals: Dict) -> bool:
        return True
        # return bool(self.ATA_EXCHANGE_NODE_NAME)
            
    def ata_exchange_add_to_queue(self):
        for record in self:
            self.env['ata.exchange.queue'].add_to_queue(record)
    # endregion

    def ata_exchange_notification(self, message: str, type: str = "mail.mt_note"):
        for record in self:
            if isinstance(record, MailThread):
                record.message_post(
                    body = message,
                    subtype_xmlid = type)

    def ata_exchange_compute_methods(self) -> List[AtaExchangeMethod]:
        return []
    
    def ata_exchange_get_ref_from_record(self) -> Union[str, None]:
                
        self.ensure_one()
        return "%s,%s" % (self._name, self.id) if self else None

    def ata_exchange_validate(self, method: AtaExchangeMethod) -> List[str]:
        return []

    def ata_exchange_validate_main(self, method: AtaExchangeMethod) -> bool:
        # перевірка заповненості полів в екземплярі моделі
        result = self.ata_exchange_validate(method)
        if method.notification_validation and result:
            self.ata_exchange_notification(
                "Validation error when queuing exchange:<br/><ul><li>%s</li></ul>"
                % "</li><br/><li>".join(result))
                
        return not result

    def ata_exchange_get_request_data(self, method: AtaExchangeMethod) -> Union[List[Dict], Dict, str]:
        # as_node - якщо запитуємо дані для кореневої ноди, то в залежності від статусу об'єкта
        # пакет даних може бути пустим. Це робиться для зменшення розміру пакетів обміну
        return data if (data:=self.ata_exchange_get_data_record(method = method, as_node = True)) else {}

    @abstractmethod
    def ata_exchange_get_data_record(self, method: AtaExchangeMethod, as_node = False) -> Union[List[Dict], Dict, str]:
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
    def ata_exchange_get_request_body(self, method: AtaExchangeMethod, request_data: Union[List[Dict], Dict, str]) -> Dict:
        return {
            **self.get_meta_data(),
            "data": request_data,
        }    

    @api.model
    def ata_exchange_response_body_parse(self, method: AtaExchangeMethod, response_body: ExtResponse) -> Tuple[Dict, bool]:
        # typical parse response
        response_data: dict = response_body['result_json'] or {}
        result = response_data.get("status", False)

        return response_data, result

    def ata_exchange_response_post_processing(self, method: AtaExchangeMethod, response_data: dict) -> bool:
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
