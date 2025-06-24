{
    'name': 'Exchange between systems. XLSX Parser Extension',
    'summary': 'Provides a utility for parsing XLSX files.',
    'description': """
This module provides an abstract model to handle XLSX file parsing.

It uses the pandas library to read and process Excel files, offering a flexible way to extract data.

Key Features:

*   Parses XLSX files into a pandas DataFrame.
*   Allows specifying rows to skip at the beginning of the file.
*   Maps Excel columns to specific field names.
*   Validates the presence of required columns.
*   Designed to be inherited by other models that need to process XLSX data as part of an exchange workflow.
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
    'external_dependencies': {
        'python': ['openpyxl', 'pandas'],
    },
    'installable': True,
}
