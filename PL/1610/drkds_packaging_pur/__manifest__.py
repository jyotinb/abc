{
    'name': 'Packaging Receipt Automation',
    'version': '1.0',
    'summary': 'Automate the receipt of products in standard packaging',
    'category': 'Inventory',
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'depends': ['purchase', 'stock'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/stock_picking_views.xml',
        'views/package_wizard_views.xml'
    ],
    'installable': True,
    'application': False,
}
