from odoo import api, models, fields, Command
from abc import abstractmethod
from typing import Tuple, List, Union, Dict, cast
from collections import namedtuple
from functools import wraps
from datetime import date, datetime
import logging

from .ata_exchange_method import AtaExchangeMethod as ExMethod
from .ata_exchange_system import ExtRequest
from odoo.addons.mail.models.mail_thread import MailThread

ExchangeResult = namedtuple('ExchangeResult', ['success', 'delete_queue', 'error'])
_logger = logging.getLogger(__name__)


class AtaExchangeClass(models.AbstractModel):
    _name = "ata.exchange.class"
    _description = "Exchange class extension"

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
        return bool(self.ATA_EXCHANGE_NODE_NAME)
            
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

    def ata_exchange_compute_methods(self) -> List[ExMethod]:
        return []
    
    def ata_exchange_get_ref_from_record(self) -> Union[str, None]:
                
        self.ensure_one()
        return "%s,%s" % (self._name, self.id) if self else None

    def ata_exchange_validate(self, method: ExMethod) -> List[str]:
        return []

    def ata_exchange_validate_main(self, method: ExMethod) -> bool:
        # перевірка заповненості полів в екземплярі моделі
        result = self.ata_exchange_validate(method)
        if method.notification_validation and result:
            self.ata_exchange_notification(
                "Validation error when queuing exchange:<br/><ul><li>%s</li></ul>"
                % "</li><br/><li>".join(result))
                
        return not result

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

    #_inherit = ['ata.exchange.method.mixing']

    @api.model
    def get_default_lang(self):
        return 'en_US'

    # region re-exchanged
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
    def exchange_outgoing_data(self, record:AtaExchangeClass, method: ExMethod) -> ExchangeResult:
        # повертаємо 2 статуси:
        # 1 - що обмін пройшов вдало (для подальших нотифікацій)
        #    - коли запис пройшов валідацію
        #    - коли є хоча б одна зовнішня система для обміну
        #    - коли обмін на всі зовнішні системи пройшов вдало
        # 2 - чи потрібно видаляти запис з черги
        #    - коли запис не пройшов валідацію
        #    - коли немає зовнішних систем для обміну
        #    - коли обмін на всі зовнішні системи пройшов вдало
        result_exchange = False
        results_ext_systems = []
        result_delete = True
        error = ""

        self = self.with_context(lang=self.get_default_lang())

        # 1. отримуємо методи обміну для запису перед самим обміном
        # (з часу постановки в чергу він міг змінитися)
        # якщо нашого методу немає в списку - вважаємо, то обмін не потрібно робити, запис - видаляється з черги
        if method in record.ata_exchange_compute_methods():
            # 2. Необхідно перевірити заповненість полів
            # якщо валідація негативна - видаляємо з черги,
            # нотифікації по результатам валідації описуємо в модулі прикладної моделі
            if record.ata_exchange_validate_main(method):
                # 3. отримуємо зовніші системи для обміну з урахуванням фільтрів, що в них є.
                # Для кожної зовнішньої системи запускаємо окремий обмін
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
                        if response_body and isinstance(response_body, dict):
                            error = response_body.get("error", False)
                            if not error:
                                # parse response body
                                response_data, result_response_body_parse = record.ata_exchange_response_body_parse(method, response_body)
                                if result_response_body_parse:
                                    # post-processing response data
                                    self._re_exchanged_add(record)
                                    result = record.ata_exchange_response_post_processing(method, response_data)
                                    self._re_exchanged_delete(record)
                        else:
                            error = "Failed to receive a response from ext. systems"
                    else:
                        error = "Request data is empty"

                    results_ext_systems.append(result)

                result_exchange = bool(results_ext_systems) and all(results_ext_systems)
                result_delete = all(results_ext_systems)
        
        return ExchangeResult(success=result_exchange, delete_queue=result_delete, error=error)

    def cron_exchange(self):
        #start outgoing queue
        self.env['ata.exchange.queue'].exchange()
        
        #start request_data
        methods = self.env['ata.exchange.method'].search([
            ('type', '=', 'request_data'),
            ('start_over_cron', '=', True)
        ])
        self.env['ata.exchange.base.requestdata'].ata_exchange_requestdata(methods)
