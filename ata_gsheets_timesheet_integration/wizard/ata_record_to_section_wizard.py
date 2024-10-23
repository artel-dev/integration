from odoo import _, api, fields, models


class GsheetTimesheetSectionWizard(models.TransientModel):
    _name = 'gsheet.timesheet.section.wizard'

    message = fields.Text(string='Message', readonly=True)
    active_ids = fields.Many2many(
        comodel_name='project.task',
        string='Active Tasks',
        default=lambda self: self.env.context.get('active_ids')
    )

    @api.model
    def default_get(self, fields_list):
        res = super(GsheetTimesheetSectionWizard, self).default_get(fields_list)
        res['message'] = _("Do you want to transfer data from a Section (Selection) to a Section?")
        return res

    def create_or_search_record(self):
        if not self.active_ids:
            return
        as_mng = self.env['ata.section']
        pt_mng = self.env['project.task']
        for active_id in self.active_ids.ids:
            current_record = pt_mng.browse(active_id)
            if not current_record or not current_record.ata_section:
                continue
            ata_section_value = dict(current_record._fields['ata_section'].selection).get(
                current_record.ata_section
            )
            if not ata_section_value:
                continue
            dmn = [
                ('name', '=', ata_section_value)
            ]
            existing_record = as_mng.search(dmn, limit=1)
            if existing_record:
                current_record.ata_section_id = existing_record.id
            else:
                vals = {
                    'name': ata_section_value
                }
                new_record = as_mng.create(vals)
                current_record.ata_section_id = new_record.id
