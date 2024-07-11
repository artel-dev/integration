{
    'name': 'VOIP customization',
    'summary': 'VOIP customization',
    'version': '17.0.1.0.0',
    'category': 'VOIP',
    'author': 'ToDo',
    'website': 'https://todo.ltd',
    'license': 'OPL-1',
    'depends': [
        'voip',
        'web'
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            "ata_voip/static/src/**/*",
        ],
    },
}
