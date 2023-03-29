{
    'name': 'Integration: Jira',
    'summary': """
Integration: Jira
Loading projects, tasks, timesheets
    """,

    'author': 'Igor Kutko',
    'website': 'https://www.it-artel.ua',
    'category': 'project',
    'version': '15.0.1.0.0',

    'depends': [
        'project',
        'hr_timesheet',
    ],

    'data': [
        'security/ata_jira_groups.xml',
        'security/ata_exchange_log_security.xml',
        'security/ir.model.access.csv',
        'views/ata_jira_menus.xml',
        'views/ata_external_system_views.xml',
        'views/ata_external_system_user_views.xml',
        'views/ata_external_service_views.xml',
        'views/ata_external_service_parameter_views.xml',
        'views/ata_exchange_log_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'wizard/ata_external_request_views.xml',
        'wizard/ata_jira_issue_views.xml',
        'wizard/ata_jira_worklog_views.xml',
        'wizard/ata_jira_comment_views.xml',
        'wizard/ata_exchange_views.xml',
        'report/ata_planned_workload_report_templates.xml',
        'report/ata_planned_workload_report_views.xml',
        'report/ata_task_report_views.xml',
    ],

    'demo': [
        'data/ata_external_system_demo.xml',
        'data/ata_external_service_demo.xml',
        'data/ata_external_service_parameter_demo.xml',
    ],
    'license': 'LGPL-3',

}
