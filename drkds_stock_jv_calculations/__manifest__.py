{
    'name': 'Stock JV Calculations',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Calculate raw material requirements for multiple products considering multilevel BOMs',
    'description': """
This module allows you to:
- Input a list of products and quantities
- Calculate the total raw material requirements
- Account for multilevel BOMs
- View summarized material requirements
    """,
    'author': 'DRKDS',
    'website': 'https://www.drkds.com',
    'depends': ['base', 'stock', 'mrp', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_jv_calculation_views.xml',
        'views/stock_jv_calculation_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}