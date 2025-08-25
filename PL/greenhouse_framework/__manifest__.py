# -*- coding: utf-8 -*-
{
    'name': 'Greenhouse Framework',
    'version': '17.0.1.0.0',
    'summary': 'Dynamic Excel-like Greenhouse Project Management Framework',
    'description': '''
        Greenhouse Project Management Framework
        ========================================
        
        A dynamic, Excel-like framework for managing greenhouse projects with:
        
        * Multiple greenhouse types (NVPH, Tunnel, Fan&Pad, etc.)
        * Dynamic section management based on greenhouse type
        * Excel-like multi-tab input/output interface
        * Automatic calculations with inter-section dependencies
        * Dependency graph with topological sort
        * Simple and non-technical user interface
        
        Features:
        - Dynamic section tabs based on greenhouse type
        - Input values organized by sections
        - Component results with automatic calculations
        - Inter-section dependency handling
        - Excel-like user experience
    ''',
    'category': 'Manufacturing',
    'author': 'Greenhouse Framework',
    'website': 'https://www.greenhouse-framework.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/section_templates.xml',
        'data/component_calculations.xml',
        'data/greenhouse_types.xml',
        'views/greenhouse_config_views.xml',
        'views/greenhouse_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'greenhouse_framework/static/src/js/section_widget.js',
            'greenhouse_framework/static/src/css/greenhouse.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}