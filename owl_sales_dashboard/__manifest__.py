{
    'name': 'Owl Sales Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Modern Sales Dashboard using OWL',
    'description': """
    Modern Sales Dashboard built with OWL framework:
    - Key performance indicators for sales analysis
    - Top products and sales people visualization
    - Monthly sales tracking
    - Customer order analysis
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 
        'web', 
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'owl_sales_dashboard/static/src/css/dashboard.css',
            'owl_sales_dashboard/static/src/js/components/kpi_card.js',
            'owl_sales_dashboard/static/src/js/components/chart_renderer.js',
            'owl_sales_dashboard/static/src/js/owl_sales_dashboard.js',
            'owl_sales_dashboard/static/src/xml/kpi_card.xml',
            'owl_sales_dashboard/static/src/xml/chart_renderer.xml',
            'owl_sales_dashboard/static/src/xml/owl_sales_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False
}