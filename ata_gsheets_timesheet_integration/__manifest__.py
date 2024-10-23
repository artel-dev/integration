{
    'name': 'Google sheets timesheet integration',
    'summary': 'Google sheets timesheet integration',
    'version': '17.0.1.1.0',
    'author': 'ToDo',
    'website': 'https://todo.ltd',
    'license': 'OPL-1',
    'category': 'Other',
    'images': [
        'static/description/banner.png',
    ],
    'depends': [
        'hr_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/ata_synchronization_wizard_views.xml',
        'views/project_task_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/ata_record_to_section_wizard_views.xml',
    ],
    'installable': 'True',
    'application': False,
}
