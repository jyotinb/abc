{
    'name': 'Bank Payments Management',
    'version': '1.0',
    'summary': 'Manage bank payments with multiple partner selection',
    'description': """
        This module allows to manage bank payments:
        * Create bank accounts for partners
        * Create payment sheets with multiple partners at once
        * Export payment data to Excel
        * Custom access rights management
    """,
    'category': 'Accounting',
    'author': 'DRKDS',
    'website': '',
    'depends': ['base', 'contacts', 'mail'],
    'data': [
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/bank_account_views.xml',
        'views/payment_sheet_views.xml',
        'views/payment_sheet_line_form.xml',
        'views/menu_views.xml',
        'reports/payment_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}