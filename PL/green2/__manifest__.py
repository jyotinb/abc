{
    'name': 'Greenhouse Management System',
    'version': '17.0.1.0.0',
    'summary': 'Advanced greenhouse component management with Excel-style interface',
    'category': 'Manufacturing',
    'website': 'http://www.drkdsinfo.com/',
    'description': """
        Advanced Greenhouse Management System
        =====================================
        
        This module provides comprehensive greenhouse structure management with:
        
        * Excel-style component management with tabular views
        * Automated component calculations based on structure dimensions  
        * Section-wise component organization (ASC, Frame, Truss, Lower Section)
        * Pipe management with detailed specifications
        * Cost calculations and reporting
        * Professional PDF reports with detailed breakdowns
        * Real-time calculations and updates
        
        Features:
        ---------
        * Component Line Management with pipe specifications
        * Automated quantity and length calculations
        * Cost analysis and totals
        * Excel-style editable grids
        * Professional reporting
        * Multi-section organization
    """,
    'author': 'drkds',
    'license': 'LGPL-3',
    'currency': 'USD',
    'price': 0.0,
    'depends': ['base', 'mail'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Master Data
        'data/pipe_type_data.xml',
        'data/pipe_size_data.xml', 
        'data/pipe_wall_thickness_data.xml',
        'data/length_master_data.xml',
        'data/sample_pipe_data.xml',
        
        # Views
        'views/green_master_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
}