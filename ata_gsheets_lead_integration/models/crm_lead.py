from odoo import models, fields, SUPERUSER_ID
import datetime
import logging
import json

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

_logger = logging.getLogger('google_sheet')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def create_opportunity(self, row):
        ata_targeted = dict(row._fields['ata_targeted'].selection).get(
            row.ata_targeted)
        lost = row.probability > 0 or row.active

        import_dict = {
            'id': row.id,
            'create_date': datetime.datetime.strftime(row.create_date,
                                                      '%d.%m.%Y') if row.create_date else '',
            'date_conversion': datetime.datetime.strftime(row.date_conversion,
                                                          '%d.%m.%Y') if row.date_conversion else '',
            'last_change_stage': '',
            'name_stage_before': '',
            'company_id': row.company_id.name if row.company_id else '',
            'team_id': row.team_id.name if row.team_id else '',
            'user_id': row.user_id.name if row.user_id else '',
            'ata_leadgen_id': row.ata_leadgen_id.name if row.ata_leadgen_id else '',
            'stage_id': row.stage_id.name if row.stage_id else '',
            'ata_targeted': ata_targeted if ata_targeted else '',
            'medium_id': row.medium_id.name if row.medium_id else '',
            'source_id': row.source_id.name if row.source_id else '',
            'lost': not lost,
            'lost_reason_id': row.lost_reason_id.name if row.lost_reason_id else '',
        }
        try:
            self.write_lead_to_google_sheet(
                import_dict,
                row.type,
                action='create'
            )
        except Exception as exc:
            _logger.error(f"create error: {exc}")

    def write_lead_to_google_sheet(self, vals, page, action='create',):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_spreadsheet_id = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_spreadsheet_id')
        ata_credentials = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_credentials')
        ata_page_name = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_page_lead_name' if page == 'lead' else 'ata_gsheets_lead_integration.ata_lead_page_opportunity_name')

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

        if page == 'lead':
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=ata_spreadsheet_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {"range": f"{ata_page_name}!A{row}:K",
                         "majorDimension": "ROWS",
                         "values": [[
                             vals['id'] if action != 'unlink' else '',
                             vals['create_date'] if action != 'unlink' else '',
                             vals['user_id'] if action != 'unlink' else '',
                             vals['ata_leadgen_id'] if action != 'unlink' else '',
                             vals['company_id'] if action != 'unlink' else '',
                             vals['team_id'] if action != 'unlink' else '',
                             vals['medium_id'] if action != 'unlink' else '',
                             vals['source_id'] if action != 'unlink' else '',
                             vals['lost'] if action != 'unlink' else '',
                             vals['ata_targeted'] if action != 'unlink' else '',
                             vals['lost_reason_id'] if action != 'unlink' else '',
                         ]]}]}).execute()
        else:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=ata_spreadsheet_id,
                body={
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {"range": f"{ata_page_name}!A{row}:O",
                         "majorDimension": "ROWS",
                         "values": [[
                             vals['id'] if action != 'unlink' else '',
                             vals['create_date'] if action != 'unlink' else '',
                             vals['date_conversion'] if action != 'unlink' else '',
                             vals['last_change_stage'] if action != 'unlink' else '',
                             vals['name_stage_before'] if action != 'unlink' else '',
                             vals['company_id'] if action != 'unlink' else '',
                             vals['team_id'] if action != 'unlink' else '',
                             vals['user_id'] if action != 'unlink' else '',
                             vals['ata_leadgen_id'] if action != 'unlink' else '',
                             vals['stage_id'] if action != 'unlink' else '',
                             vals['ata_targeted'] if action != 'unlink' else '',
                             vals['medium_id'] if action != 'unlink' else '',
                             vals['source_id'] if action != 'unlink' else '',
                             vals['lost'] if action != 'unlink' else '',
                             vals['lost_reason_id'] if action != 'unlink' else '',
                         ]]}]}).execute()

    def write(self, vals):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_active')

        old_stage = False
        if 'stage_id' in vals:
            old_stage = self.stage_id.name

        res = super().write(vals)

        if not ata_active:
            return res

        if 'type' in vals:
            self.create_opportunity(self)

        lead_and_opportunity = False
        super_self = self.with_user(SUPERUSER_ID)
        for message in super_self.message_ids:
            if message.tracking_value_ids:
                for value_id in message.tracking_value_ids:
                    if value_id.field_id.name == 'type':
                        lead_and_opportunity = True

        if self.type == 'lead' or lead_and_opportunity:
            field_list = [
                'create_date',
                'user_id',
                'ata_leadgen_id',
                'company_id',
                'team_id',
                'medium_id',
                'source_id',
                'probability',
                'active',
                'ata_targeted',
                'lost_reason_id',
            ]
            if any(x in vals for x in field_list):
                ata_targeted = dict(self._fields['ata_targeted'].selection).get(
                    self.ata_targeted)
                lost = self.probability > 0 or self.active

                import_dict = {
                    'id': self.id,
                    'create_date': datetime.datetime.strftime(self.create_date,'%d.%m.%Y') if self.create_date else '',
                    'user_id': self.user_id.name if self.user_id else '',
                    'ata_leadgen_id': self.ata_leadgen_id.name if self.ata_leadgen_id else '',
                    'company_id': self.company_id.name if self.company_id else '',
                    'team_id': self.team_id.name if self.team_id else '',
                    'medium_id': self.medium_id.name if self.medium_id else '',
                    'source_id': self.source_id.name if self.source_id else '',
                    'lost': not lost,
                    'ata_targeted': ata_targeted if ata_targeted else '',
                    'lost_reason_id': self.lost_reason_id.name if self.lost_reason_id else '',
                }
                try:
                    self.write_lead_to_google_sheet(
                        import_dict,
                        'lead',
                        action='write'
                    )
                except Exception as exc:
                    _logger.error(f"write error: {exc}")
        if self.type == 'opportunity' or lead_and_opportunity:
            field_list = [
                'create_date',
                'date_conversion',
                'company_id',
                'team_id',
                'user_id',
                'ata_leadgen_id',
                'stage_id',
                'ata_targeted',
                'medium_id',
                'source_id',
                'active',
                'lost_reason_id',
            ]
            if any(x in vals for x in field_list):
                ata_targeted = dict(
                    self._fields['ata_targeted'].selection).get(
                    self.ata_targeted)
                lost = self.probability > 0 or self.active

                import_dict = {
                    'id': self.id,
                    'create_date': datetime.datetime.strftime(self.create_date,
                                                              '%d.%m.%Y') if self.create_date else '',
                    'date_conversion': datetime.datetime.strftime(self.date_conversion,
                                                              '%d.%m.%Y') if self.date_conversion else '',
                    'last_change_stage': datetime.datetime.strftime(fields.datetime.now(), '%d.%m.%Y') if old_stage else '',
                    'name_stage_before': old_stage if old_stage else '',
                    'company_id': self.company_id.name if self.company_id else '',
                    'team_id': self.team_id.name if self.team_id else '',
                    'user_id': self.user_id.name if self.user_id else '',
                    'ata_leadgen_id': self.ata_leadgen_id.name if self.ata_leadgen_id else '',
                    'stage_id': self.stage_id.name if self.stage_id else '',
                    'ata_targeted': ata_targeted if ata_targeted else '',
                    'medium_id': self.medium_id.name if self.medium_id else '',
                    'source_id': self.source_id.name if self.source_id else '',
                    'lost': not lost,
                    'lost_reason_id': self.lost_reason_id.name if self.lost_reason_id else '',
                }
                try:
                    self.write_lead_to_google_sheet(
                        import_dict,
                        'opportunity',
                        action='write'
                    )
                except Exception as exc:
                    _logger.error(f"write error: {exc}")
        return res

    def create(self, vals_list):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_active')

        res = super().create(vals_list)
        if not ata_active:
            return res

        for row in res:
            if row.type == 'lead':
                ata_targeted = dict(row._fields['ata_targeted'].selection).get(row.ata_targeted)
                lost = row.probability > 0 or row.active

                import_dict = {
                    'id': row.id,
                    'create_date': datetime.datetime.strftime(row.create_date,
                                                              '%d.%m.%Y') if row.create_date else '',
                    'user_id': row.user_id.name if row.user_id else '',
                    'ata_leadgen_id': row.ata_leadgen_id.name if row.ata_leadgen_id else '',
                    'company_id': row.company_id.name if row.company_id else '',
                    'team_id': row.team_id.name if row.team_id else '',
                    'medium_id': row.medium_id.name if row.medium_id else '',
                    'source_id': row.source_id.name if row.source_id else '',
                    'lost': not lost,
                    'ata_targeted': ata_targeted if ata_targeted else '',
                    'lost_reason_id': row.lost_reason_id.name if row.lost_reason_id else '',
                }
                try:
                    self.write_lead_to_google_sheet(
                        import_dict,
                        row.type,
                        action='create'
                    )
                except Exception as exc:
                    _logger.error(f"create error: {exc}")
            else:
                self.create_opportunity(row)

        return res

    def unlink(self):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_active')

        if ata_active:
            for rec in self:
                import_dict = {'id': rec.id}
                try:
                    self.write_lead_to_google_sheet(
                        import_dict,
                        self.type,
                        action='unlink'
                    )
                except Exception as exc:
                    _logger.error(f"unlink error: {exc}")
        super().unlink()
