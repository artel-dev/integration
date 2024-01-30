from odoo import models
import datetime
import logging
import json

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

_logger = logging.getLogger('google_sheet')


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def write_timesheet_to_google_sheet(self, vals, action='create'):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_spreadsheet_id = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_spreadsheet_id')
        ata_credentials = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_credentials')
        ata_page_name = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_page_name')

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
                    {"range": f"{ata_page_name}!A{row}:I",
                     "majorDimension": "ROWS",
                     "values": [[
                         vals['id'] if action != 'unlink' else '',
                         vals['date'] if action != 'unlink' else '',
                         vals['project'] if action != 'unlink' else '',
                         vals['task'] if action != 'unlink' else '',
                         vals['section'] if action != 'unlink' else '',
                         vals['description'] if action != 'unlink' else '',
                         vals['unit_amount'] if action != 'unlink' else '',
                         vals['employee'] if action != 'unlink' else '',
                         vals['partner'] if action != 'unlink' else '',
                     ]]}]}).execute()

    def write(self, vals):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_active')

        res = super().write(vals)
        if not ata_active:
            return res

        field_list = [
            'date',
            'employee_id',
            'name',
            'unit_amount',
            'task_id',
            'project_id'
        ]
        if any(x in vals for x in field_list):
            section = dict(self.task_id._fields['ata_section'].selection).get(
                self.task_id.ata_section)

            import_dict = {
                'id': self.id,
                'date': datetime.datetime.strftime(
                    self.date,
                    '%d.%m.%Y'
                ),
                'project': self.project_id.name,
                'task': self.task_id.name,
                'section': section if section else '',
                'description': self.name,
                'unit_amount': self.unit_amount,
                'employee': self.employee_id.name,
                'partner': self.partner_id.name if self.partner_id else '',
            }
            try:
                self.write_timesheet_to_google_sheet(
                    import_dict,
                    action='write'
                )
            except Exception as exc:
                _logger.error(f"write error: {exc}")
        return res

    def create(self, vals_list):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_active')

        res = super().create(vals_list)
        if not ata_active:
            return res

        for row in res:
            section = dict(row.task_id._fields['ata_section'].selection).get(
                row.task_id.ata_section)

            import_dict = {
                'id': row.id,
                'date': datetime.datetime.strftime(
                    row.date,
                    '%d.%m.%Y'
                ),
                'project': row.project_id.name,
                'task': row.task_id.name,
                'section': section if section else '',
                'description': row.name,
                'unit_amount': row.unit_amount,
                'employee': row.employee_id.name,
                'partner': row.partner_id.name if row.partner_id else '',
            }
            try:
                self.write_timesheet_to_google_sheet(
                    import_dict,
                    action='create'
                )
            except Exception as exc:
                _logger.error(f"create error: {exc}")
        return res

    def unlink(self):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_active = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_active')

        if ata_active:
            for rec in self:
                import_dict = {'id': rec.id}
                try:
                    self.write_timesheet_to_google_sheet(
                        import_dict,
                        action='unlink'
                    )
                except Exception as exc:
                    _logger.error(f"unlink error: {exc}")
        super().unlink()
