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
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param('ata_gsheets_lead_integration.ata_lead_active')

        dt = datetime.datetime
        done_date = fields.datetime.now()
        done_date_fmt = dt.strftime(done_date, '%d.%m.%Y') if done_date else ''

        activities = list()
        res_models = list()
        for record in self:
            import_dict = dict()
            import_dict['activity_type_id'] = (
                record.activity_type_id.name if record.activity_type_id else ''
            )
            import_dict['date'] = done_date_fmt
            activities.append(import_dict)
            res_models.append(record.res_model)

        # res = super()._action_done(feedback=feedback, attachment_ids=attachment_ids)
        messages, next_activities = super()._action_done(
            feedback=feedback, attachment_ids=attachment_ids)

        if 'crm.lead' not in res_models or not ata_active:
            return messages, next_activities

        # if isinstance(res, tuple):
        #     if res[0] and res[0]._name == 'mail.message':
        #         import_dict['id'] = res[0].id
        #         import_dict['user_id'] = res[0].author_id.name if res[0].author_id else ''
        # else:
        #     _logger.error(f"res don't contain 'mail.message'")
        #     return res

        if messages and messages._name == 'mail.message':
            for import_dict, res_model, message in zip(
                    activities, res_models, messages):
                if res_model != 'crm.lead':
                    continue
                import_dict['id'] = message.id
                import_dict['user_id'] = (
                    message.author_id.name if message.author_id else ''
                )
                try:
                    self.write_lead_to_google_sheet(
                        import_dict,
                        action='create'
                    )
                except Exception as exc:
                    _logger.error(f"unlink error: {exc}")
        else:
            _logger.error(f"res don't contain 'mail.message'")
            return messages, next_activities

        # if ata_active:
        #     try:
        #         self.write_lead_to_google_sheet(
        #             import_dict,
        #             action='create'
        #         )
        #     except Exception as exc:
        #         _logger.error(f"unlink error: {exc}")

        return messages, next_activities
