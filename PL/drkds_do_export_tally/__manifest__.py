{
    'name': 'Delivery Order Export to Tally',
    'version': '1.0',
    'summary': 'Export delivery order details in Tally-compatible format',
    'description': """
        This module allows exporting delivery order details to CSV in a format
        that can be imported into Tally accounting software.
        Export includes sales order number, customer name, product, quantity, 
        and price formatted for Tally import.
    """,
    'category': 'Inventory',
    'author': 'DRKDS',
    'website': 'https://www.drkds.com',
    'depends': ['stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/export_delivery_wizard_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}