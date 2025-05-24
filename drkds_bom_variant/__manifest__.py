# -*- coding: utf-8 -*-
{
    'name': 'BoM Variant Management',
    'version': '1.0',
    'summary': 'Apply BoM on product variants in Odoo Community',
    'description': """
        This module extends the Bills of Materials functionality in Odoo Community Edition to:
        - Apply BoMs on specific product variants
        - Manage variant-specific manufacturing flows
        - Enable a complete process from sales to dispatch for product variants
        - Track all changes with detailed logs
    """,
    'category': 'Manufacturing',
    'author': 'DRKDS',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'mrp',
        'sale',
        'sale_management',
        'sale_stock',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/drkds_bom_sequence.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'wizards/bom_variant_apply_wizard_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
