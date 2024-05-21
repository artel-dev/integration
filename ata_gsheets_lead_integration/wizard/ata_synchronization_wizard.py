from odoo import fields, models
import logging
import datetime
import json

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

_logger = logging.getLogger('google_sheet_synchronization')


def lead_to_gsheet(row, values, service, spreadsheet_id, page_name, column):
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"{page_name}!A{row}:{column}",
                 "majorDimension": "ROWS",
                 "values": values}]}).execute()


class GsheetLeadSyncWizard(models.TransientModel):
    _name = 'gsheet.lead.sync.wizard'
    _description = 'Sync lead with google sheet'

    ata_date_form = fields.Date(
        string='Date form',
        required=True
    )
    ata_date_to = fields.Date(
        string='Date to',
        required=True
    )
    ata_type = fields.Selection(
        string='Type',
        required=True,
        selection=[
            ('lead', 'Lead'),
            ('opportunity', 'Opportunity'),
        ]
    )

    def google_authorization(self):
        with_user = self.env['ir.config_parameter'].sudo()
        ata_spreadsheet_id = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_spreadsheet_id')
        ata_credentials = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_credentials')
        ata_page_name = with_user.get_param(
            'ata_gsheets_lead_integration.ata_lead_page_lead_name' if self.ata_type == 'lead' else 'ata_gsheets_lead_integration.ata_lead_page_opportunity_name')
        ata_column_max = 'K' if self.ata_type == 'lead' else 'M'

        ata_credentials = json.loads(ata_credentials)

        # Авторизуемся и получаем service — экземпляр доступа к API
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            ata_credentials,
            ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build(
            'sheets', 'v4', http=httpAuth)
        return ata_spreadsheet_id, ata_page_name, service, ata_column_max

    def google_lead_sync(self):
        spreadsheet_id, page_name, service, column_max = self.google_authorization()

        try:
            values = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{page_name}!A1:A',
                majorDimension='COLUMNS'
            ).execute()
            if 'values' in values:
                values = values['values'][0]
            else:
                values = []

            _logger.info(f"got ids from google sheet")

            row = len(values) + 1

            crm_lead = self.env['crm.lead'].sudo()
            domain = ['&', ('create_date', '>=', self.ata_date_form),
                           ('create_date', '<=', self.ata_date_to),
                           ('type', '=', self.ata_type)]
            res = crm_lead.search(domain)

            ids = []
            for line_id in res.ids:
                if str(line_id) not in values:
                    ids.append(line_id)

            res = crm_lead.browse(ids)

            _logger.info(f"loading leads len({len(res)}) to google sheet")

            values = []
            if self.ata_type == 'lead':
                for line_id in res:
                    ata_targeted = dict(
                        line_id._fields['ata_targeted'].selection).get(
                        line_id.ata_targeted)
                    lost = line_id.probability > 0 or line_id.active

                    values.append([
                        line_id.id,
                        datetime.datetime.strftime(
                            line_id.create_date,
                            '%d.%m.%Y'
                        ) if line_id.create_date else '',
                        line_id.user_id.name if line_id.user_id else '',
                        line_id.ata_leadgen_id.name if line_id.ata_leadgen_id else '',
                        line_id.company_id.name if line_id.company_id else '',
                        line_id.team_id.name if line_id.team_id else '',
                        line_id.medium_id.name if line_id.medium_id else '',
                        line_id.source_id.name if line_id.source_id else '',
                        not lost,
                        ata_targeted if ata_targeted else '',
                        line_id.lost_reason_id.name if line_id.lost_reason_id else '',
                    ])

                if len(values) >= 100:
                    lead_to_gsheet(
                        row, values, service,
                        spreadsheet_id, page_name, column_max)
                    row += len(values)
                    _logger.info(
                        f"loaded timesheet len({len(values)}) to google sheet")
                    values = []
            else:
                for line_id in res:
                    ata_targeted = dict(
                        line_id._fields['ata_targeted'].selection).get(
                        line_id.ata_targeted)

                    old_stage = False
                    old_stage_date = False
                    for message in line_id.message_ids:
                        if message.tracking_value_ids:
                            for tracking_value in message.tracking_value_ids:
                                if tracking_value.field.name == 'stage_id':
                                    old_stage = tracking_value.old_value_char
                                    old_stage_date = message.create_date

                            if old_stage:
                                break

                    values.append([
                        line_id.id,
                        datetime.datetime.strftime(line_id.create_date,'%d.%m.%Y') if line_id.create_date else '',
                        datetime.datetime.strftime(line_id.date_conversion,'%d.%m.%Y') if line_id.date_conversion else '',
                        datetime.datetime.strftime(old_stage_date,'%d.%m.%Y') if old_stage_date else '',
                        old_stage if old_stage else '',
                        line_id.company_id.name if line_id.company_id else '',
                        line_id.team_id.name if line_id.team_id else '',
                        line_id.user_id.name if line_id.user_id else '',
                        line_id.ata_leadgen_id.name if line_id.ata_leadgen_id else '',
                        line_id.stage_id.name if line_id.stage_id else '',
                        ata_targeted if ata_targeted else '',
                        line_id.medium_id.name if line_id.medium_id else '',
                        line_id.source_id.name if line_id.source_id else '',
                    ])

                if len(values) >= 100:
                    lead_to_gsheet(
                        row, values, service,
                        spreadsheet_id, page_name, column_max)
                    row += len(values)
                    _logger.info(
                        f"loaded timesheet len({len(values)}) to google sheet")
                    values = []
            if values:
                lead_to_gsheet(
                    row, values, service, spreadsheet_id, page_name, column_max)
                _logger.info(
                    f"loaded timesheet len({len(values)}) to google sheet")
        except Exception as exc:
            _logger.error(f"synchronization error: {exc}")
