{
    'name': 'DRKDS Greenhouse Management System',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Complete Greenhouse Management System with Component Calculation',
    'description': """
        DRKDS Greenhouse Management System
        ==================================
        
        Complete greenhouse project management system with:
        * Automated component calculations based on structure parameters
        * Pipe management with specifications and costing
        * Accessories management with profile calculations
        * Professional Excel and PDF reporting
        * Project duplication and selection preservation
        * Real-time cost calculations
        * Extensible section and component system
    """,
    'author': 'DRKDS',
    'website': 'https://www.drkds.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/pipe_type_data.xml',
        'data/pipe_size_data.xml',
        'data/pipe_wall_thickness_data.xml',
        'data/length_master_data.xml',
        'data/accessories_master_data.xml',
        'data/sample_pipe_data.xml',
        
        # Views
        'views/green_master_views.xml',
        'views/component_line_views.xml',
        'views/accessories_views.xml',
        'views/pipe_management_views.xml',
        'views/length_master_views.xml',
        'views/menu_views.xml',
        
        # Reports
        'reports/report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'drkds_green/static/src/css/greenhouse.css',
            'drkds_green/static/src/js/greenhouse.js',
        ],
    },
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}