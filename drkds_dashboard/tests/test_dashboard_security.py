from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestDrkdsDashboardSecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        # Setup test users
        self.user_group = self.env.ref('drkds_dashboard.group_drkds_dashboard_user')
        self.manager_group = self.env.ref('drkds_dashboard.group_drkds_dashboard_manager')

    def test_user_access_rights(self):
        # Test basic user access
        test_user = self.env['res.users'].create({
            'name': 'Dashboard User',
            'login': 'dashboard_user',
            'groups_id': [(6, 0, [self.user_group.id])]
        })

        # Check access to dashboard models
        with self.assertRaises(AccessError):
            self.env['drkds.dashboard.metric'].with_user(test_user).create({
                'name': 'Forbidden Metric',
                'model_name': 'sale.order',
                'metric_type': 'count'
            })