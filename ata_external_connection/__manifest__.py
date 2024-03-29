{
    'name': 'External connection',
    'summary': 'External connection',
    'version': '16.0.1.0.4',
    'author': 'ToDo',
    'website': 'it-artel.ua',
    'license': 'OPL-1',
    'category': 'Integration',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ata_external_connection_menus.xml',
        'views/ata_external_connection_domain.xml',
        'views/ata_external_system_views.xml',
        'views/ata_exchange_log_views.xml',
        'views/ata_exchange_queue_views.xml',
        'views/ata_exchange_queue_usage_views.xml',
        'data/ata_exchange_queue_cron.xml',
    ],
    'installable': 'True',
}
