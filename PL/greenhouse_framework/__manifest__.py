# -*- coding: utf-8 -*-
{
    'name': 'Greenhouse Framework',
    'version': '17.0.1.0.0',
    'summary': 'Simple Excel-like Greenhouse Project Management Framework',
    'description': '''
        Greenhouse Project Management Framework
        ========================================
        
        A simple, Excel-like framework for managing greenhouse projects with:
        
        * Multiple greenhouse types (NVPH, Tunnel, Fan&Pad)
        * Dynamic section management
        * Excel-like input/output interface
        * Automatic calculations
        * Simple and non-technical user interface
        
        Week 1 Features:
        - Basic project management
        - Input value storage
        - Component result storage
        - Simple UI like Excel
    ''',
    'category': 'Manufacturing',
    'author': 'Greenhouse Framework',
    'website': 'https://www.greenhouse-framework.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/section_templates.xml',
        'data/component_calculations.xml',
        'data/greenhouse_types.xml',
        'views/greenhouse_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
