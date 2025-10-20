{
    'name': 'Simple Package Selection',
    'version': '1.0',
    'category': 'Inventory/Delivery',
    'summary': 'Select packages in delivery orders',
    'description': """
Simple Package Selection
=======================
This module adds a wizard that allows users to easily select packages when processing delivery orders.
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/package_selection_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}