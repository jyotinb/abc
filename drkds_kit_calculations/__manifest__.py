{
    'name': 'DRKDS Kit Calculations',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Dynamic Cost Sheet Calculator with Configurable Formulas',
    'description': '''
        Complete cost calculation system for kit-based products with:
        - Multi-level user access (4 levels)
        - Configurable formulas and templates
        - Component enable/disable functionality
        - Comprehensive change logging
        - Integration with Odoo contacts
        - Real-time calculations
        - Template management
        - Price management
    ''',
    'author': 'DRKDS Solutions',
    'website': 'https://www.drkds.com',
    'depends': ['base', 'contacts'],
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequences.xml',
        'data/component_categories.xml',
        'data/default_components.xml',
        
        # Views
        'views/menu_views.xml',
        'views/component_views.xml',
        'views/template_views.xml',
        'views/cost_sheet_views.xml',
        'views/change_log_views.xml',
        'views/dashboard_views.xml',
        
        # Wizards
        'wizard/cost_sheet_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'drkds_kit_calculations/static/src/css/cost_sheet.css',
            'drkds_kit_calculations/static/src/js/cost_sheet_widget.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}