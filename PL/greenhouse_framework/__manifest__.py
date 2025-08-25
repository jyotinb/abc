# -*- coding: utf-8 -*-
{
    'name': 'Greenhouse Framework',
    'version': '17.0.1.0.0',
    'summary': 'Dynamic Excel-like Greenhouse Project Management Framework',
    'description': '''Greenhouse Project Management Framework''',
    'category': 'Manufacturing',
    'author': 'Greenhouse Framework',
    'website': 'https://www.greenhouse-framework.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/section_templates_minimal.xml',      # Minimal sections
        'data/component_calculations_minimal.xml', # Empty calculations
        'data/greenhouse_types_minimal.xml',       # Minimal types
        'views/complete_greenhouse_views.xml',
        'views/greenhouse_config_views_fixed.xml',
        'views/menu_structure.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}