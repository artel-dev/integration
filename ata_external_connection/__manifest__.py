{
    'name': 'External connection',
    'summary': 'External connection',
    'version': '16.0.2.0.9',
    'author': 'ToDo',
    'website': 'it-artel.ua',
    'license': 'OPL-1',
    'category': 'Integration/Base',
    'depends': [
        'base',
    ],
    'data': [
        'data/ata_exchange_category.xml',
        'data/ata_exchange_queue_cron.xml',
        'security/ir.model.access.csv',
        'views/ata_external_connection_menus.xml',
        'views/ata_external_connection_domain.xml',
        'views/ata_external_system_views.xml',
        'views/ata_exchange_log_views.xml',
        'views/ata_exchange_queue_views.xml',
        'views/ata_exchange_queue_usage_views.xml',      
    ],
    'installable': 'True',
}
