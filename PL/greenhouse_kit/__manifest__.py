{
    'name': 'Greenhouse Kit Calculations',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Dynamic greenhouse structure calculations with modular sections',
    'description': """
        Greenhouse Kit Calculations Module
        ================================
        
        Features:
        * Multiple greenhouse types (NVPH, Tunnel, etc.)
        * Dynamic sections with dependencies
        * Configurable input and calculated fields
        * Advanced formula engine with cross-section references
        * Material quantity tracking
        * Project-based calculations
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/greenhouse_sections_data.xml',
        'data/greenhouse_fields_data.xml',
        'data/greenhouse_types_data.xml',
        
        'views/greenhouse_type_views.xml',
        'views/greenhouse_section_template_views.xml',
        'views/greenhouse_field_template_views.xml',
        'views/greenhouse_project_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
