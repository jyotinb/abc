{
    'name': 'Greenhouse Management System - Complete',
    'version': '17.0.2.0.0',
    'summary': 'Complete greenhouse component management with Excel-style interface and all 35+ components',
    'category': 'Manufacturing',
    'website': 'http://www.drkdsinfo.com/',
    'description': """
        Complete Greenhouse Management System
        ====================================
        
        This module provides comprehensive greenhouse structure management with:
        
        * Excel-style component management with tabular views
        * Complete automated component calculations (35+ component types)
        * Section-wise component organization (ASC, Frame, Truss, Lower Section)
        * Pipe management with detailed specifications and cost calculations
        * Professional PDF reports with detailed breakdowns
        * Real-time calculations and cost updates
        * Modern Odoo 17 compatible interface
        
        Features:
        ---------
        * Complete Component Coverage: All 35+ component types from greenhouse industry
        * Excel-Style Interface: Familiar tabular editing with inline calculations
        * Automated Calculations: Input basic dimensions, get complete material list
        * Cost Analysis: Real-time cost calculations with pipe specifications
        * Professional Reports: Clean, detailed PDF reports for customers
        * Section Organization: ASC, Frame, Truss, and Lower section management
        * Length Master: Configurable component lengths for flexibility
        * Pipe Catalog: Complete pipe management with types, sizes, and rates
        
        Component Coverage:
        ------------------
        * ASC Components (5 types): Hockey supports, corridor pipes
        * Frame Components (4 types): Columns (main, middle, thick, quadruple)
        * Truss Components (18 types): Arches, bottom chords, supports, purlins
        * Lower Section (15 types): Screens, cross bracing, gutters, accessories
        
        Technical Features:
        ------------------
        * Modern Architecture: Component line model for scalability
        * Odoo 17 Compatible: Latest syntax and best practices
        * Performance Optimized: Efficient calculations and database design
        * Extensible: Easy to add new component types
        * Maintainable: Clean, documented code structure
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
    'images': ['static/description/banner.png'],
}