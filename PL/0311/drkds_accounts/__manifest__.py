{
    'name': 'DRKDS Complete Accounting Suite',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Complete Professional Accounting Suite',
    'description': '''
        Complete Accounting Suite with Financial Reports, Budget Management,
        Asset Management, Payment Processing, Analytics, and Advanced Features
    ''',
    'author': 'DRKDS',
    'website': 'https://www.drkds.com',
    'license': 'LGPL-3',
    'depends': ['account', 'base', 'web'],
    'data': [
        # Security - Load first
        'security/ir.model.access.csv',
        
        # Data - Load second
        'data/ir_sequence_data.xml',
        
        # Views - Load third (models exist, no actions yet)
        'views/budget_views.xml',
        'views/asset_views.xml',
        
        # Wizards - Load fourth (creates actions)
        'wizard/general_ledger_view.xml',
        'wizard/trial_balance_view.xml',
        
        # Menus - Load LAST (references actions)
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
