from odoo.tests.common import TransactionCase

class TestDrkdsDashboardExport(TransactionCase):
    def setUp(self):
        super().setUp()
        # Setup test data
        self.export_model = self.env['drkds.dashboard.export']
        self.template_model = self.env['drkds.dashboard.template']

    def test_export_creation(self):
        # Create test dashboard data
        test_data = {
            'metrics': {
                'total_sales': 1000,
                'average_order': 50
            }
        }

        # Test CSV export
        export = self.export_model.create_export(test_data, 'csv')
        
        self.assertTrue(export.exists())
        self.assertEqual(export.export_format, 'csv')
        self.assertTrue(export.file_content)