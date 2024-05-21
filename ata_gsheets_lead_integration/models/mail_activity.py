from odoo import models, fields
import datetime
import logging
import json

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

_logger = logging.getLogger('google_sheet')


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def write_lead_to_google_sheet(self, vals, action='create',):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_spreadsheet_id = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_spreadsheet_id')
        ata_credentials = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_credentials')
        ata_page_name = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_page_action_name')

        ata_credentials = json.loads(ata_credentials)

        try:
            # Авторизуемся и получаем service — экземпляр доступа к API
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                ata_credentials,
                ['https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive'])
            httpAuth = credentials.authorize(httplib2.Http())
            service = apiclient.discovery.build(
                'sheets', 'v4', http=httpAuth)
        except Exception as exc:
            _logger.error(f"create google service error: {exc}")
            return

        values = service.spreadsheets().values().get(
            spreadsheetId=ata_spreadsheet_id,
            range=f'{ata_page_name}!A1:A',
            majorDimension='ROWS'
        ).execute()
        values = values['values']

        if action == 'create':
            row = len(values) + 1
        else:
            row = values.index([str(vals['id'])]) + 1

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=ata_spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": f"{ata_page_name}!A{row}:D",
                     "majorDimension": "ROWS",
                     "values": [[
                         vals['id'] if action != 'unlink' else '',
                         vals['activity_type_id'] if action != 'unlink' else '',
                         vals['user_id'] if action != 'unlink' else '',
                         vals['date'] if action != 'unlink' else '',
                     ]]}]}).execute()

    def _action_done(self, feedback=False, attachment_ids=None):
        import_dict = {
            'id': self.id,
            'activity_type_id': self.activity_type_id.name if self.activity_type_id else '',
            'user_id': self.user_id.name if self.user_id else '',
            'date': datetime.datetime.strftime(fields.datetime.now(),
                                               '%d.%m.%Y') if fields.datetime.now() else '',
        }
        res_model = self.res_model

        res = super()._action_done(feedback=feedback, attachment_ids=attachment_ids)

        if res_model != 'crm.lead':
            return res

        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param('ata_gsheets_lead_integration.ata_lead_active')

        if ata_active:
            try:
                self.write_lead_to_google_sheet(
                    import_dict,
                    action='create'
                )
            except Exception as exc:
                _logger.error(f"unlink error: {exc}")

        return res
