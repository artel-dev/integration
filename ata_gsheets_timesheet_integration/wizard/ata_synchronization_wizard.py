from odoo import fields, models
import logging
import datetime
import json

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

_logger = logging.getLogger('google_sheet_synchronization')


def timesheet_to_gsheet(row, values, service, spreadsheet_id, page_name):
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"{page_name}!A{row}:H",
                 "majorDimension": "ROWS",
                 "values": values}]}).execute()


class GsheetTimesheetSyncWizard(models.TransientModel):
    _name = 'gsheet.timesheet.sync.wizard'
    _description = 'Sync timesheet with google sheet'

    ata_date_form = fields.Date(
        string='Date form',
        required=True
    )
    ata_date_to = fields.Date(
        string='Date to',
        required=True
    )

    def google_authorization(self):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_spreadsheet_id = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_spreadsheet_id')
        ata_credentials = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_credentials')
        ata_page_name = with_user.get_param(
            'ata_google_sheet_timesheet_integration.ata_page_name')

        ata_credentials = json.loads(ata_credentials)

        # Авторизуемся и получаем service — экземпляр доступа к API
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            ata_credentials,
            ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build(
            'sheets', 'v4', http=httpAuth)
        return ata_spreadsheet_id, ata_page_name, service

    def google_timesheet_sync(self):
        spreadsheet_id, page_name, service = self.google_authorization()

        try:
            values = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{page_name}!A1:A',
                majorDimension='COLUMNS'
            ).execute()
            values = values['values'][0]

            _logger.info(f"got ids from google sheet")

            row = len(values) + 1

            account_analytic_line = self.env['account.analytic.line'].sudo()
            domain = ['&', ('date', '>=', self.ata_date_form),
                           ('date', '<=', self.ata_date_to)]
            res = account_analytic_line.search(domain)

            ids = []
            for line_id in res.ids:
                if str(line_id) not in values:
                    ids.append(line_id)

            res = account_analytic_line.browse(ids)

            _logger.info(f"loading timesheet len({len(res)}) to google sheet")

            values = []
            for line_id in res:
                section = dict(
                    line_id.task_id._fields['ata_section'].selection).get(
                    line_id.task_id.ata_section)

                values.append([
                    line_id.id,
                    datetime.datetime.strftime(
                        line_id.date,
                        '%d.%m.%Y'
                    ) if line_id.date else '',
                    line_id.project_id.name if line_id.project_id else '',
                    line_id.task_id.name if line_id.task_id else '',
                    section if section else '',
                    line_id.name,
                    line_id.unit_amount,
                    line_id.employee_id.name if line_id.employee_id else '',
                    line_id.partner_id.name if line_id.partner_id else '',
                ])

                if len(values) >= 100:
                    timesheet_to_gsheet(
                        row, values, service,
                        spreadsheet_id, page_name)
                    row += len(values)
                    _logger.info(
                        f"loaded timesheet len({len(values)}) to google sheet")
                    values = []
            if values:
                timesheet_to_gsheet(
                    row, values, service, spreadsheet_id, page_name)
                _logger.info(
                    f"loaded timesheet len({len(values)}) to google sheet")
        except Exception as exc:
            _logger.error(f"synchronization error: {exc}")
