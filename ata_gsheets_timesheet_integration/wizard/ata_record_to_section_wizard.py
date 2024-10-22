from odoo import models, fields, api


class GsheetTimesheetSectionWizard(models.TransientModel):
    _name = 'gsheet.timesheet.section.wizard'

    message = fields.Text(string='Message', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(GsheetTimesheetSectionWizard, self).default_get(fields_list)
        res['message'] = self._context.get('message', '')
        return res

    def create_or_select_record(self):
        active_ids = self._context.get('active_ids')
        if active_ids:
            for active_id in active_ids:
                current_record = self.env['project.task'].browse(active_id)
                if current_record and current_record.ata_section:
                    ata_section_value = dict(current_record._fields['ata_section'].selection).get(
                        current_record.ata_section)
                    if ata_section_value:
                        existing_record = self.env['section.name'].search([('name', '=', ata_section_value)],
                                                                          limit=1)
                        if existing_record:
                            current_record.ata_section_name = existing_record.id
                        else:
                            new_record = self.env['section.name'].create({'name': ata_section_value})
                            current_record.ata_section_name = new_record.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super(GsheetTimesheetSectionWizard, self).create(vals_list)
        for record in records:
            record.create_or_select_record()
        return records
