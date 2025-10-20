{
    'name': 'DRKDS Packing List',
    'version': '1.0',
    'category': 'Inventory/Delivery',
    'summary': 'Custom Packing List Report for Delivery Orders',
    'description': """
    Custom module for printing Packing List from Delivery Order.
    Features:
    - Header: Packing List with Total Gross Weight and Total Packages
    - Fields: Invoice No (manual input), SO No, DO No, Dispatch Date
    - Product listing with package information
    """,
    'author': 'DRKDS',
    'website': 'https://www.drkds.com',
    'depends': ['stock', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'report/drkds_packing_list_report.xml',
        'views/report_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}