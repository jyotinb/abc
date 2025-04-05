from odoo.tests.common import TransactionCase

class TestDrkdsDashboardMetrics(TransactionCase):
    def setUp(self):
        super().setUp()
        # Setup test data
        self.metric_model = self.env['drkds.dashboard.metric']

    def test_metric_creation(self):
        # Test creating a simple count metric
        metric = self.metric_model.create({
            'name': 'Test Sales Count',
            'model_name': 'sale.order',
            'metric_type': 'count'
        })

        self.assertTrue(metric.exists())
        self.assertEqual(metric.name, 'Test Sales Count')
        self.assertEqual(metric.metric_type, 'count')

    def test_metric_calculation(self):
        # Test metric calculation
        metric = self.metric_model.create({
            'name': 'Test Sales Amount',
            'model_name': 'sale.order',
            'metric_type': 'sum',
            'field_name': 'amount_total'
        })

        # Calculation will depend on existing sale orders
        result = metric.calculate_metric()
        self.assertIsNotNone(result)