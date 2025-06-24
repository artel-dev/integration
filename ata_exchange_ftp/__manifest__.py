{
    'name': 'Exchange between systems. FTP Extension',
    'summary': 'Adds FTP support for the Data Exchange module.',
    'description': """
This module extends the 'Data Exchange' functionality to allow integration with FTP servers.
Key features:
- Configure FTP connections (server, port, credentials).
- Test the connection to the FTP server directly from Odoo.
- List and download files from specified directories.
- Automatically create folders and move files on the FTP server.
- Seamlessly integrates into the existing exchange system workflows.
    """,
    'version': '17.0.1.4.0',
    'author': 'ToDo',
    'website': 'https://todo.ltd',
    'license': 'OPL-1',
    'category': 'Integration/Extension',
    'depends': [
        'ata_exchange_v4',
    ],
    'data': [],
    'external_dependencies': {},
    'installable': True,
}
