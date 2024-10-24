from odoo import api, fields, models
from odoo.tools import safe_eval

from .ata_external_connection_method import AtaExternalConnectionMethod as ExtMethod
from .ata_external_connection_base import AtaExternalConnectionClass as ExtClass
from .ata_external_system import ExternalSystem as ExtSystem



class AtaExternalConnectionDomain(models.Model):
    _name = "ata.external.connection.domain"
    _description = "Domain for search external system"
    _inherit = ['ata.external.connection.method.mixing']

    domain = fields.Char(
        string="Domain",)
    ext_system = fields.Many2one(
        comodel_name="ata.external.system",
        string="External system",
        required=True,)
    
    @api.model
    def get_ext_systems(self, record:ExtClass, method: ExtMethod) -> list[ExtSystem]:
        ext_systems = []
        self_sudo = self.sudo()
        
        # 1. check ext. system without analysis record data
        records_domain = self_sudo.search([
            ('method', '=', method.id),
            ('ext_system.disabled', '=', False)
        ])

        # 2. check record data for compliance with the domain
        for record_domain in records_domain:
            if record_domain.domain:
                _domain = safe_eval.safe_eval(record_domain.domain, self._get_eval_context())
                if record.filtered_domain(_domain).with_env(record.env):
                    ext_systems.append(record_domain.ext_system)
            else:
                ext_systems.append(record_domain.ext_system)

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
