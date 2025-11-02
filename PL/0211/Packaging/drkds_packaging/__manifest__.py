{
    'name': 'Auto Multi-Level BOM Cost Update',
    'version': '1.0',
    'summary': 'Automatically update product costs based on multi-level BOMs',
    'author': 'Your Name',
    'category': 'Manufacturing',
    'depends': ['stock','stock_delivery','mrp', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'views/packaging_wizard_views.xml',
        'views/stock_picking_view.xml',
        'data/ir_sequence_data.xml',  # Add this line to include the sequence definition
    ],
    'installable': True,
    'application': False,
}
