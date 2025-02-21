from odoo import _, api, fields, models


class AtaRecordSectionWizard(models.TransientModel):
    _name = 'ata.record.section.wizard'
    _description = 'Record section wizard'

    @api.model
    def default_get(self, fields_list):
        res = super(AtaRecordSectionWizard, self).default_get(fields_list)
        tasks_ids = self.env.context.get('active_ids')
        if tasks_ids:
            res['tasks_ids'] = [(6, 0, tasks_ids)]
        res['message'] = _("Do you want to transfer data from a Section (Selection) to a Section?")
        return res

    message = fields.Text(string='Message', readonly=True)
    tasks_ids = fields.Many2many(
        comodel_name='project.task',
        string='Tasks'
    )

    def create_or_search_record(self):
        if not self.tasks_ids:
            return
        as_mng = self.env['ata.section']
        pt_mng = self.env['project.task']

        for task_id in self.tasks_ids.ids:
            current_record = pt_mng.browse(task_id)
            if current_record and current_record.ata_section:
                ata_section_value = dict(current_record._fields['ata_section'].selection).get(
                    current_record.ata_section
                )
                if ata_section_value:
                    self._update_section(as_mng, current_record, ata_section_value)
            for subtask in current_record.child_ids:
                if subtask.ata_section:
                    ata_section_value = dict(subtask._fields['ata_section'].selection).get(
                        subtask.ata_section
                    )
                    if ata_section_value:
                        self._update_section(as_mng, subtask, ata_section_value)

    @staticmethod
    def _update_section(as_mng, task_record, ata_section_value):
        dmn = [('name', '=', ata_section_value)]
        existing_record = as_mng.search(dmn, limit=1)
        if existing_record:
            task_record.ata_section_id = existing_record.id
        else:
            vals = {
                'name': ata_section_value
            }
            new_record = as_mng.create(vals)
            task_record.ata_section_id = new_record.id
