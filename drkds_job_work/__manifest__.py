{
    'name': 'DRKDS Job Work Management',
    'version': '1.0',
    'category': 'Manufacturing/Job Work',
    'summary': 'Manage Job Work Operations',
    'description': """
        Job Work Management System
        - Quotation with Job Work Products
        - BOM based Raw Material Receipt
        - Manufacturing Orders
        - Finished Goods Delivery
    """,
    'depends': [
        'base',
        'sale_management',
        'stock',
        'mrp',
    ],
    'data': [
        'security/job_work_security.xml',
        'security/ir.model.access.csv',
        'views/job_work_views.xml',
        'views/sale_views.xml',
        'views/stock_views.xml',
        'views/mrp_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}