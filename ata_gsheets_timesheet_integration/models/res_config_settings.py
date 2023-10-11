from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ata_spreadsheet_id = fields.Char(
        string='Spreadsheet id'
    )
    ata_credentials = fields.Char(
        string='Credentials'
    )
    ata_page_name = fields.Char(
        string='Page name'
    )
    ata_active = fields.Boolean(
        string='Active'
    )

    def set_values(self):
        res = super().set_values()
        conf = self.env['ir.config_parameter'].sudo()
        param1 = 'ata_google_sheet_timesheet_integration.ata_spreadsheet_id'
        param2 = 'ata_google_sheet_timesheet_integration.ata_credentials'
        param3 = 'ata_google_sheet_timesheet_integration.ata_page_name'
        param4 = 'ata_google_sheet_timesheet_integration.ata_active'
        conf.set_param(param1, self.ata_spreadsheet_id)
        conf.set_param(param2, self.ata_credentials)
        conf.set_param(param3, self.ata_page_name)
        conf.set_param(param4, self.ata_active)
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        ata_spreadsheet_id = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_spreadsheet_id')
        ata_credentials = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_credentials')
        ata_page_name = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_page_name')
        ata_active = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_active')
        res.update(
            ata_spreadsheet_id=ata_spreadsheet_id,
            ata_credentials=ata_credentials,
            ata_page_name=ata_page_name,
            ata_active=ata_active,
        )
        return res
