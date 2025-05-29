from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import json

class Dashboard(models.TransientModel):
    _name = 'drkds.dashboard'
    _description = 'DRKDS Dashboard'
    
    # Summary Statistics
    total_cost_sheets = fields.Integer(string='Total Cost Sheets', compute='_compute_statistics')
    confirmed_cost_sheets = fields.Integer(string='Confirmed Cost Sheets', compute='_compute_statistics')
    active_components = fields.Integer(string='Active Components', compute='_compute_statistics')
    active_templates = fields.Integer(string='Active Templates', compute='_compute_statistics')
    
    # Financial Statistics
    total_cost_value = fields.Float(string='Total Cost Value', compute='_compute_financial_stats')
    average_cost_value = fields.Float(string='Average Cost Value', compute='_compute_financial_stats')
    
    # System Health (Admin only)
    active_users_count = fields.Integer(string='Active Users', compute='_compute_system_health')
    recent_changes_count = fields.Integer(string='Recent Changes', compute='_compute_system_health')
    calculations_count = fields.Integer(string='Calculations', compute='_compute_system_health')
    
    # Recent Activity
    recent_cost_sheets = fields.One2many('drkds.cost.sheet', compute='_compute_recent_activity')
    
    # Charts Data
    cost_sheets_by_status_chart = fields.Text(string='Cost Sheets by Status', compute='_compute_charts')
    monthly_activity_chart = fields.Text(string='Monthly Activity', compute='_compute_charts')
    
    @api.depends_context('uid')
    def _compute_statistics(self):
        for record in self:
            # Total cost sheets
            record.total_cost_sheets = self.env['drkds.cost.sheet'].search_count([])
            
            # Confirmed cost sheets
            record.confirmed_cost_sheets = self.env['drkds.cost.sheet'].search_count([
                ('state', '=', 'confirmed')
            ])
            
            # Active components
            record.active_components = self.env['drkds.kit.component'].search_count([
                ('active', '=', True)
            ])
            
            # Active templates
            record.active_templates = self.env['drkds.cost.template'].search_count([
                ('active', '=', True)
            ])
    
    @api.depends_context('uid')
    def _compute_financial_stats(self):
        for record in self:
            cost_sheets = self.env['drkds.cost.sheet'].search([
                ('state', 'in', ['calculated', 'confirmed'])
            ])
            
            if cost_sheets:
                total_value = sum(cost_sheets.mapped('enabled_components_total'))
                record.total_cost_value = total_value
                record.average_cost_value = total_value / len(cost_sheets)
            else:
                record.total_cost_value = 0.0
                record.average_cost_value = 0.0
    
    @api.depends_context('uid')
    def _compute_system_health(self):
        for record in self:
            # Only compute for admin users
            if not self.env.user.has_group('drkds_kit_calculations.group_admin'):
                record.active_users_count = 0
                record.recent_changes_count = 0
                record.calculations_count = 0
                continue
            
            # Active users in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            active_user_logs = self.env['drkds.change.log'].search([
                ('create_date', '>=', thirty_days_ago)
            ])
            record.active_users_count = len(set(active_user_logs.mapped('user_id.id')))
            
            # Recent changes in last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            record.recent_changes_count = self.env['drkds.change.log'].search_count([
                ('create_date', '>=', seven_days_ago)
            ])
            
            # Calculations in last 30 days
            record.calculations_count = self.env['drkds.change.log'].search_count([
                ('create_date', '>=', thirty_days_ago),
                ('action_type', '=', 'calculation')
            ])
    
    @api.depends_context('uid')
    def _compute_recent_activity(self):
        for record in self:
            # Get recent cost sheets (last 10)
            recent_sheets = self.env['drkds.cost.sheet'].search([], 
                                                               order='create_date desc', 
                                                               limit=10)
            # Note: This is a computed field, so we can't actually assign Many2many
            # In the view, we'll use a different approach
            record.recent_cost_sheets = False
    
    @api.depends_context('uid')
    def _compute_charts(self):
        for record in self:
            # Cost sheets by status chart
            status_data = {}
            sheets_by_status = self.env['drkds.cost.sheet'].read_group(
                [], ['state'], ['state']
            )
            for group in sheets_by_status:
                status_data[group['state']] = group['state_count']
            
            record.cost_sheets_by_status_chart = json.dumps({
                'type': 'pie',
                'data': {
                    'labels': list(status_data.keys()),
                    'datasets': [{
                        'data': list(status_data.values()),
                        'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                    }]
                }
            })
            
            # Monthly activity chart (last 6 months)
            six_months_ago = datetime.now() - timedelta(days=180)
            monthly_data = self.env['drkds.cost.sheet'].read_group([
                ('create_date', '>=', six_months_ago)
            ], ['create_date'], ['create_date:month'])
            
            months = [group['create_date:month'] for group in monthly_data]
            counts = [group['create_date_count'] for group in monthly_data]
            
            record.monthly_activity_chart = json.dumps({
                'type': 'line',
                'data': {
                    'labels': months,
                    'datasets': [{
                        'label': 'Cost Sheets Created',
                        'data': counts,
                        'borderColor': '#36A2EB',
                        'fill': False
                    }]
                }
            })
    
    def action_create_cost_sheet(self):
        """Quick action to create new cost sheet"""
        return {
            'name': _('Create Cost Sheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.cost.sheet.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_create_template(self):
        """Quick action to create new template"""
        return {
            'name': _('Create Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.template.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
    
    @api.model
    def get_recent_cost_sheets(self):
        """Get recent cost sheets for dashboard display"""
        return self.env['drkds.cost.sheet'].search([], 
                                                  order='create_date desc', 
                                                  limit=10)

class CostAnalysis(models.Model):
    _name = 'drkds.cost.analysis'
    _description = 'Cost Analysis Report'
    _auto = False
    _order = 'total_amount desc'
    
    client_id = fields.Many2one('res.partner', string='Client', readonly=True)
    template_type = fields.Char(string='Template Type', readonly=True)
    cost_sheet_count = fields.Integer(string='Cost Sheets', readonly=True)
    total_amount = fields.Float(string='Total Amount', readonly=True)
    average_amount = fields.Float(string='Average Amount', readonly=True)
    min_amount = fields.Float(string='Min Amount', readonly=True)
    max_amount = fields.Float(string='Max Amount', readonly=True)
    date_range = fields.Char(string='Date Range', readonly=True)
    
    def init(self):
        from odoo import tools
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    cs.client_id,
                    ct.template_type,
                    COUNT(cs.id) as cost_sheet_count,
                    SUM(cs.enabled_components_total) as total_amount,
                    AVG(cs.enabled_components_total) as average_amount,
                    MIN(cs.enabled_components_total) as min_amount,
                    MAX(cs.enabled_components_total) as max_amount,
                    CONCAT(
                        TO_CHAR(MIN(cs.create_date), 'YYYY-MM-DD'), 
                        ' to ', 
                        TO_CHAR(MAX(cs.create_date), 'YYYY-MM-DD')
                    ) as date_range
                FROM drkds_cost_sheet cs
                JOIN drkds_cost_template ct ON cs.template_id = ct.id
                WHERE cs.state IN ('calculated', 'confirmed')
                GROUP BY cs.client_id, ct.template_type
            )
        """ % self._table)

class ComponentUsage(models.Model):
    _name = 'drkds.component.usage'
    _description = 'Component Usage Analysis'
    _auto = False
    _order = 'usage_count desc'
    
    component_id = fields.Many2one('drkds.kit.component', string='Component', readonly=True)
    component_category = fields.Char(string='Category', readonly=True)
    usage_count = fields.Integer(string='Usage Count', readonly=True)
    total_quantity = fields.Float(string='Total Quantity', readonly=True)
    total_amount = fields.Float(string='Total Amount', readonly=True)
    average_rate = fields.Float(string='Average Rate', readonly=True)
    templates_used = fields.Integer(string='Templates Used', readonly=True)
    
    def init(self):
        from odoo import tools
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    bl.component_id,
                    cc.name as component_category,
                    COUNT(bl.id) as usage_count,
                    SUM(bl.quantity) as total_quantity,
                    SUM(bl.amount) as total_amount,
                    AVG(bl.rate) as average_rate,
                    COUNT(DISTINCT cs.template_id) as templates_used
                FROM drkds_cost_bom_line bl
                JOIN drkds_cost_sheet cs ON bl.cost_sheet_id = cs.id
                JOIN drkds_kit_component kc ON bl.component_id = kc.id
                LEFT JOIN drkds_component_category cc ON kc.category_id = cc.id
                WHERE bl.is_enabled = true 
                AND cs.state IN ('calculated', 'confirmed')
                GROUP BY bl.component_id, cc.name
            )
        """ % self._table)

class UserActivity(models.TransientModel):
    _name = 'drkds.user.activity'
    _description = 'User Activity Dashboard'
    
    # Summary fields
    total_users = fields.Integer(string='Total Users', compute='_compute_user_stats')
    active_users = fields.Integer(string='Active Users', compute='_compute_user_stats')
    cost_sheets_created = fields.Integer(string='Cost Sheets Created', compute='_compute_user_stats')
    calculations_performed = fields.Integer(string='Calculations Performed', compute='_compute_user_stats')
    
    # Detail lines
    user_activity_lines = fields.One2many('drkds.user.activity.line', 'activity_id', 
                                         string='User Activity Details', compute='_compute_activity_lines')
    
    @api.depends_context('uid')
    def _compute_user_stats(self):
        for record in self:
            # Only for admin users
            if not self.env.user.has_group('drkds_kit_calculations.group_admin'):
                record.total_users = 0
                record.active_users = 0
                record.cost_sheets_created = 0
                record.calculations_performed = 0
                continue
            
            # Total users with DRKDS access
            drkds_users = self.env['res.users'].search([
                ('groups_id', 'in', [
                    self.env.ref('drkds_kit_calculations.group_simple_user').id,
                    self.env.ref('drkds_kit_calculations.group_pricelist_manager').id,
                    self.env.ref('drkds_kit_calculations.group_template_manager').id,
                    self.env.ref('drkds_kit_calculations.group_admin').id,
                ])
            ])
            record.total_users = len(drkds_users)
            
            # Active users (with activity in last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            active_logs = self.env['drkds.change.log'].search([
                ('create_date', '>=', thirty_days_ago),
                ('user_id', 'in', drkds_users.ids)
            ])
            record.active_users = len(set(active_logs.mapped('user_id.id')))
            
            # Cost sheets created in last 30 days
            record.cost_sheets_created = self.env['drkds.cost.sheet'].search_count([
                ('create_date', '>=', thirty_days_ago)
            ])
            
            # Calculations performed in last 30 days
            record.calculations_performed = self.env['drkds.change.log'].search_count([
                ('create_date', '>=', thirty_days_ago),
                ('action_type', '=', 'calculation')
            ])
    
    @api.depends_context('uid')
    def _compute_activity_lines(self):
        for record in self:
            # This would need to be implemented properly in a real scenario
            record.user_activity_lines = False

class UserActivityLine(models.TransientModel):
    _name = 'drkds.user.activity.line'
    _description = 'User Activity Line'
    
    activity_id = fields.Many2one('drkds.user.activity', string='Activity Dashboard')
    user_id = fields.Many2one('res.users', string='User')
    cost_sheets_count = fields.Integer(string='Cost Sheets')
    calculations_count = fields.Integer(string='Calculations')
    components_toggled = fields.Integer(string='Components Toggled')
    last_activity = fields.Datetime(string='Last Activity')
    user_group = fields.Char(string='User Group')

# Report Models for Advanced Analytics
class MonthlyActivityReport(models.Model):
    _name = 'drkds.monthly.activity'
    _description = 'Monthly Activity Report'
    _auto = False
    _order = 'month desc'
    
    month = fields.Date(string='Month', readonly=True)
    cost_sheets_created = fields.Integer(string='Cost Sheets Created', readonly=True)
    calculations_performed = fields.Integer(string='Calculations Performed', readonly=True)
    components_toggled = fields.Integer(string='Components Toggled', readonly=True)
    active_users = fields.Integer(string='Active Users', readonly=True)
    total_cost_value = fields.Float(string='Total Cost Value', readonly=True)
    
    def init(self):
        from odoo import tools
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    DATE_TRUNC('month', cs.create_date)::date as month,
                    COUNT(DISTINCT cs.id) as cost_sheets_created,
                    COUNT(DISTINCT CASE WHEN cl.action_type = 'calculation' THEN cl.id END) as calculations_performed,
                    COUNT(DISTINCT CASE WHEN cl.action_type = 'toggle' THEN cl.id END) as components_toggled,
                    COUNT(DISTINCT cl.user_id) as active_users,
                    SUM(cs.enabled_components_total) as total_cost_value
                FROM drkds_cost_sheet cs
                LEFT JOIN drkds_change_log cl ON DATE_TRUNC('month', cl.create_date) = DATE_TRUNC('month', cs.create_date)
                WHERE cs.create_date >= (CURRENT_DATE - INTERVAL '12 months')
                GROUP BY DATE_TRUNC('month', cs.create_date)
            )
        """ % self._table)

class ClientAnalysisReport(models.Model):
    _name = 'drkds.client.analysis'
    _description = 'Client Analysis Report'
    _auto = False
    _order = 'total_value desc'
    
    client_id = fields.Many2one('res.partner', string='Client', readonly=True)
    cost_sheets_count = fields.Integer(string='Cost Sheets', readonly=True)
    total_value = fields.Float(string='Total Value', readonly=True)
    average_value = fields.Float(string='Average Value', readonly=True)
    confirmed_sheets = fields.Integer(string='Confirmed Sheets', readonly=True)
    draft_sheets = fields.Integer(string='Draft Sheets', readonly=True)
    first_cost_sheet = fields.Date(string='First Cost Sheet', readonly=True)
    last_cost_sheet = fields.Date(string='Last Cost Sheet', readonly=True)
    preferred_template = fields.Char(string='Preferred Template', readonly=True)
    
    def init(self):
        from odoo import tools
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    cs.client_id,
                    COUNT(cs.id) as cost_sheets_count,
                    SUM(cs.enabled_components_total) as total_value,
                    AVG(cs.enabled_components_total) as average_value,
                    COUNT(CASE WHEN cs.state = 'confirmed' THEN 1 END) as confirmed_sheets,
                    COUNT(CASE WHEN cs.state = 'draft' THEN 1 END) as draft_sheets,
                    MIN(cs.create_date::date) as first_cost_sheet,
                    MAX(cs.create_date::date) as last_cost_sheet,
                    (
                        SELECT ct.name 
                        FROM drkds_cost_template ct 
                        WHERE ct.id = (
                            SELECT template_id 
                            FROM drkds_cost_sheet 
                            WHERE client_id = cs.client_id 
                            GROUP BY template_id 
                            ORDER BY COUNT(*) DESC 
                            LIMIT 1
                        )
                    ) as preferred_template
                FROM drkds_cost_sheet cs
                GROUP BY cs.client_id
                HAVING COUNT(cs.id) > 0
            )
        """ % self._table)

# Dashboard Helper Functions
class DashboardUtils(models.AbstractModel):
    _name = 'drkds.dashboard.utils'
    _description = 'Dashboard Utility Functions'
    
    @api.model
    def get_kpi_data(self, period_days=30):
        """Get KPI data for dashboard widgets"""
        period_start = datetime.now() - timedelta(days=period_days)
        
        return {
            'cost_sheets_created': self.env['drkds.cost.sheet'].search_count([
                ('create_date', '>=', period_start)
            ]),
            'calculations_performed': self.env['drkds.change.log'].search_count([
                ('create_date', '>=', period_start),
                ('action_type', '=', 'calculation')
            ]),
            'components_toggled': self.env['drkds.change.log'].search_count([
                ('create_date', '>=', period_start),
                ('action_type', '=', 'toggle')
            ]),
            'active_users': len(set(
                self.env['drkds.change.log'].search([
                    ('create_date', '>=', period_start)
                ]).mapped('user_id.id')
            )),
            'total_cost_value': sum(
                self.env['drkds.cost.sheet'].search([
                    ('create_date', '>=', period_start),
                    ('state', 'in', ['calculated', 'confirmed'])
                ]).mapped('enabled_components_total')
            )
        }
    
    @api.model
    def get_trend_data(self, metric='cost_sheets', periods=6):
        """Get trend data for charts"""
        data = []
        for i in range(periods):
            period_start = datetime.now() - timedelta(days=30*(i+1))
            period_end = datetime.now() - timedelta(days=30*i)
            
            if metric == 'cost_sheets':
                count = self.env['drkds.cost.sheet'].search_count([
                    ('create_date', '>=', period_start),
                    ('create_date', '<', period_end)
                ])
            elif metric == 'calculations':
                count = self.env['drkds.change.log'].search_count([
                    ('create_date', '>=', period_start),
                    ('create_date', '<', period_end),
                    ('action_type', '=', 'calculation')
                ])
            else:
                count = 0
            
            data.append({
                'period': period_start.strftime('%Y-%m'),
                'value': count
            })
        
        return list(reversed(data))
    
    @api.model
    def get_user_performance_data(self):
        """Get user performance metrics"""
        if not self.env.user.has_group('drkds_kit_calculations.group_admin'):
            return []
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Get all DRKDS users
        drkds_groups = [
            'drkds_kit_calculations.group_simple_user',
            'drkds_kit_calculations.group_pricelist_manager', 
            'drkds_kit_calculations.group_template_manager',
            'drkds_kit_calculations.group_admin'
        ]
        
        users_data = []
        for group_xml_id in drkds_groups:
            try:
                group = self.env.ref(group_xml_id)
                for user in group.users:
                    # Get user activity
                    user_logs = self.env['drkds.change.log'].search([
                        ('user_id', '=', user.id),
                        ('create_date', '>=', thirty_days_ago)
                    ])
                    
                    cost_sheets = self.env['drkds.cost.sheet'].search_count([
                        ('create_uid', '=', user.id),
                        ('create_date', '>=', thirty_days_ago)
                    ])
                    
                    calculations = user_logs.filtered(lambda l: l.action_type == 'calculation')
                    toggles = user_logs.filtered(lambda l: l.action_type == 'toggle')
                    
                    users_data.append({
                        'user_name': user.name,
                        'user_group': group.name.replace('Cost Sheet ', ''),
                        'cost_sheets_created': cost_sheets,
                        'calculations_performed': len(calculations),
                        'components_toggled': len(toggles),
                        'total_activity': len(user_logs),
                        'last_activity': max(user_logs.mapped('create_date')) if user_logs else None
                    })
            except:
                continue
        
        return users_data