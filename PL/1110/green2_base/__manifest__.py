{
    'name': 'Greenhouse Management - Base',
    'version': '17.0.2.0.0',
    'summary': 'Base module for greenhouse component management',
    'category': 'Manufacturing',
    'description': '''
        Greenhouse Management Base Module
        =================================
        
        Core functionality for greenhouse structure management:
        * Customer and project information
        * Basic structure configuration
        * Component line framework
        * Pipe management system
        * Length master configuration
        * Cost calculation framework
        * Excel export functionality
        * Bulk pipe assignment tools
    ''',
    'author': 'drkds',
    'website': 'http://www.drkdsinfo.com/',
    'depends': ['base', 'mail'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/pipe_type_data.xml',
        'data/pipe_size_data.xml',
        'data/pipe_wall_thickness_data.xml',
        'data/sample_pipe_data.xml',
        'data/length_master_data.xml',
        
        # Wizard Views
        'wizard/bulk_pipe_assignment_wizard_views.xml',
        
        # Views
        'views/green_master_base_views.xml',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}