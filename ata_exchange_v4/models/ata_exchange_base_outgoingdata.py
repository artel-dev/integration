from odoo import api, models

from collections import namedtuple
from contextlib import contextmanager
from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_class  import AtaExchangeClass

ExchangeResult = namedtuple('ExchangeResult', ['success', 'delete_queue', 'error'])

class AtaExchangeBaseOutgoingdata(models.AbstractModel):
    _name = "ata.exchange.base.outgoingdata"
    _description = "Exchange base outgoing data model"

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

    @contextmanager
    def _re_exchanged_manager(self, record:AtaExchangeClass):
        self._re_exchanged_add(record)
        try:
            yield
        finally:
            self._re_exchanged_delete(record)
    # endregion

    @api.model
    def exchange_outgoing_data(self, record:AtaExchangeClass, method: AtaExchangeMethod) -> ExchangeResult:
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
        error_msg = ""

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
                        ext_request = ext_system.get_init_extrequest()
                        method.set_request_valid_codes(ext_request)
                        
                        ext_request['method']  = method
                        ext_request['name']  = f'{method.description}'
                        ext_request['exchange_id'] = record.ata_exchange_get_name()
                        ext_system.calc_url(ext_request)
                        ext_request['method_params']['request_body'] = method.get_request_body(request_data)

                        ext_system.execute(ext_request)
                        
                        if (ext_response := self.env['ata.exchange.method'].read_response_standard(ext_request)):
                            if not ext_response['error']:
                                if (response_data := method.get_response_data(ext_response)):
                                    # post-processing response data
                                    with self._re_exchanged_manager(record):
                                        result = method.response_post_processing(ext_response, response_data, record)
                                        
                                    error_msg = ext_response['error_msg']
                                else:
                                    error_msg = "Response data is empty"
                            else:
                                error_msg = ext_response['error_msg']
                                result = method.response_error_post_processing(ext_response)
                        else:
                            error_msg = "Failed to receive a response from ext. systems."
                    else:
                        error_msg = "Request data is empty"

                    results_ext_systems.append(result)

                result_exchange = bool(results_ext_systems) and all(results_ext_systems)
                result_delete = all(results_ext_systems)
        
        return ExchangeResult(success=result_exchange, delete_queue=result_delete, error=error_msg)
