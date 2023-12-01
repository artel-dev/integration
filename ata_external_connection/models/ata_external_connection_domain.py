from odoo import api, fields, models
from odoo.tools import safe_eval


class AtaExternalConnectionDomain(models.Model):
    _name = "ata.external.connection.domain"
    _description = "Domain for search external system"
    _inherit = ['ata.external.connection.method.mixing']

    domain = fields.Char(string="Domain")
    ext_system = fields.Many2one(comodel_name="ata.external.system", string="External system")

    @api.model
    def get_ext_systems(self, record, method):
        ext_systems = []
        # 1. check availability domain record
        # 2. if there are no domain records, then get all external system
        # 3. if there is only one ext. system - use it, else - nothing (why only 1 ???)

        self_sudo = self.sudo()
        if not self_sudo.search([]):
            all_ext_systems = self.env['ata.external.system'].get_all_ext_system()
            if len(all_ext_systems) == 1:
                ext_systems = all_ext_systems
        else:
            # 1a. check ext. system without analysis record data
            records_domain = self_sudo.search([
                # ('model_name', '=', record._name),
                ('method', '=', method),
                ('ext_system.disabled', '=', False)
            ])

            # 1b. check record data for compliance with the domain
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
