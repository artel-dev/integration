from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ata_lead_spreadsheet_id = fields.Char(
        string='Spreadsheet id'
    )
    ata_lead_credentials = fields.Char(
        string='Credentials'
    )
    ata_lead_page_action_name = fields.Char(
        string='Page action name',
        config_parameter='ata_gsheets_lead_integration.ata_lead_page_action_name',
    )
    ata_lead_page_lead_name = fields.Char(
        string='Page lead name',
        config_parameter='ata_gsheets_lead_integration.ata_lead_page_lead_name',
    )
    ata_lead_page_opportunity_name = fields.Char(
        string='Page opportunity name',
        config_parameter='ata_gsheets_lead_integration.ata_lead_page_opportunity_name',
    )
    ata_lead_active = fields.Boolean(
        string='Active Google Sheets - CRM Lead integration'
    )

    def set_values(self):
        res = super().set_values()
        conf = self.env['ir.config_parameter'].sudo()
        param1 = 'ata_gsheets_lead_integration.ata_lead_spreadsheet_id'
        param2 = 'ata_gsheets_lead_integration.ata_lead_credentials'
        param4 = 'ata_gsheets_lead_integration.ata_lead_active'
        conf.set_param(param1, self.ata_lead_spreadsheet_id)
        conf.set_param(param2, self.ata_lead_credentials)
        conf.set_param(param4, self.ata_lead_active)
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        ata_lead_spreadsheet_id = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_spreadsheet_id')
        ata_lead_credentials = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_credentials')
        ata_lead_active = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_active')
        res.update(
            ata_lead_spreadsheet_id=ata_lead_spreadsheet_id,
            ata_lead_credentials=ata_lead_credentials,
            ata_lead_active=ata_lead_active,
        )
        return res
