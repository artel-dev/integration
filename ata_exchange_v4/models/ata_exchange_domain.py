from odoo import api, fields, models
from odoo.tools import safe_eval
from typing import List

from .ata_exchange_method import AtaExchangeMethod as ExMethod
from .ata_exchange_base   import AtaExchangeClass  as ExClass
from .ata_exchange_system import AtaExchangeSystem as ExSystem


class AtaExchangeDomain(models.Model):
    _name = "ata.exchange.domain"
    _description = "Domain for search external system"
    _inherit = ['ata.exchange.method.mixing']

    domain = fields.Char(
        string="Domain",)
    ext_system = fields.Many2one(
        comodel_name="ata.exchange.system",
        string="External system",
        required=True,)
    
    @api.model
    def get_ext_systems(self, record:ExClass|None, method: ExMethod) -> ExSystem:
        self_sudo = self.sudo()
        
        # 1. check ext. system without analysis record data
        records_domain = self_sudo.search([
            ('method', '=', method.id),
            ('ext_system.disabled', '=', False)
        ])

        # 2. check record data for compliance with the domain
        ext_systems = self.env['ata.exchange.system']
        for record_domain in records_domain:
            if record and record_domain.domain:
                _domain = safe_eval.safe_eval(record_domain.domain, self._get_eval_context())
                if record.filtered_domain(_domain).with_env(record.env):
                    ext_systems |= record_domain.ext_system
            else:
                ext_systems |= record_domain.ext_system

        return ext_systems

    def _get_eval_context(self) -> dict:
        """ Prepare the context used when evaluating python code
            :returns: dict -- evaluation context given to safe_eval
        """
        return {
            'datetime': safe_eval.datetime,
            'dateutil': safe_eval.dateutil,
            'time': safe_eval.time,
            'uid': self.env.uid,
            'user': self.env.user,
        }

    def action_add_to_queue(self):
        _domain = safe_eval.safe_eval(self.domain, self._get_eval_context()) \
            if self.domain else []
        records = self.env[self.model_name].sudo().search(_domain)
        if isinstance(records, ExClass):
            records.ata_exchange_add_to_queue()
