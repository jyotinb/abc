{
    'name': 'Delivery Order Merge',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Merge Delivery Orders while preserving Sales Order rate data',
    'description': """
Delivery Order Merge
===================
This module allows merging of multiple delivery orders while preserving:
- The original sales order rate data
- References to original sales orders
- Proper handling of payment and delivery terms mismatches

Key features:
- Merge multiple delivery orders into one
- Preserve original price information
- Track source delivery orders
- Handle payment and delivery terms mismatches
- Select final terms for merged deliveries
    """,
    'author': 'DRKDS',
    'website': 'https://www.drkds.com',
    'depends': ['stock', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/merge_pickings_view.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}