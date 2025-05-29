from odoo import models, fields, api, _
from odoo.http import request

class ChangeLog(models.Model):
    _name = 'drkds.change.log'
    _description = 'System Change Log'
    _order = 'create_date desc'
    _rec_name = 'description'
    
    # Log Information
    user_id = fields.Many2one('res.users', string='User', required=True, 
                             default=lambda self: self.env.user)
    action_type = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('toggle', 'Toggle'),
        ('calculation', 'Calculation'),
        ('access', 'Access'),
        ('export', 'Export'),
        ('import', 'Import')
    ], string='Action Type', required=True)
    
    # Object Information
    object_model = fields.Char(string='Object Model')
    object_id = fields.Integer(string='Object ID')
    object_name = fields.Char(string='Object Name')
    
    # Change Details
    field_name = fields.Char(string='Field Changed')
    old_value = fields.Text(string='Old Value')
    new_value = fields.Text(string='New Value')
    description = fields.Text(string='Description', required=True)
    
    # Technical Details
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Text(string='User Agent')
    session_id = fields.Char(string='Session ID')
    
    # Categorization
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Severity', default='low')
    
    category = fields.Selection([
        ('security', 'Security'),
        ('data', 'Data Change'),
        ('calculation', 'Calculation'),
        ('configuration', 'Configuration'),
        ('user_action', 'User Action'),
        ('system', 'System')
    ], string='Category', default='user_action')
    
    # Additional Context
    additional_info = fields.Text(string='Additional Information')
    error_traceback = fields.Text(string='Error Traceback')
    
    # Timestamp (using create_date)
    create_date = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
    
    # Computed fields for display
    user_name = fields.Char(related='user_id.name', string='User Name', store=True)
    model_name = fields.Char(string='Model Display Name', compute='_compute_model_name')
    change_summary = fields.Char(string='Change Summary', compute='_compute_change_summary')
    
    @api.depends('object_model')
    def _compute_model_name(self):
        """Get human-readable model name"""
        for record in self:
            if record.object_model:
                try:
                    model = self.env[record.object_model]
                    record.model_name = model._description
                except:
                    record.model_name = record.object_model
            else:
                record.model_name = 'Unknown'
    
    @api.depends('action_type', 'field_name', 'object_name')
    def _compute_change_summary(self):
        """Generate a brief summary of the change"""
        for record in self:
            if record.action_type == 'create':
                record.change_summary = f"Created {record.object_name or 'record'}"
            elif record.action_type == 'update':
                field_part = f" ({record.field_name})" if record.field_name else ""
                record.change_summary = f"Updated {record.object_name or 'record'}{field_part}"
            elif record.action_type == 'delete':
                record.change_summary = f"Deleted {record.object_name or 'record'}"
            elif record.action_type == 'toggle':
                record.change_summary = f"Toggled {record.field_name or 'field'} for {record.object_name or 'record'}"
            elif record.action_type == 'calculation':
                record.change_summary = f"Calculated {record.object_name or 'values'}"
            else:
                record.change_summary = f"{record.action_type.title()} action on {record.object_name or 'record'}"
    
    @api.model
    def log_change(self, action_type, object_model=None, object_id=None, 
                   object_name=None, field_name=None, old_value=None, 
                   new_value=None, description=None, severity='low', 
                   category='user_action', additional_info=None):
        """Universal logging method"""
        
        # Determine severity automatically based on action
        if not severity or severity == 'low':
            severity = self._auto_determine_severity(action_type, object_model)
        
        # Determine category automatically
        if not category or category == 'user_action':
            category = self._auto_determine_category(action_type, field_name)
        
        vals = {
            'user_id': self.env.user.id,
            'action_type': action_type,
            'object_model': object_model,
            'object_id': object_id,
            'object_name': object_name,
            'field_name': field_name,
            'old_value': str(old_value) if old_value is not None else None,
            'new_value': str(new_value) if new_value is not None else None,
            'description': description or f"{action_type.title()} action performed",
            'severity': severity,
            'category': category,
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent(),
            'session_id': self._get_session_id(),
            'additional_info': additional_info,
        }
        
        # Create log entry
        try:
            return self.create(vals)
        except Exception as e:
            # If logging fails, at least try to log the error
            print(f"Failed to create change log: {e}")
            return False
    
    def _auto_determine_severity(self, action_type, object_model):
        """Automatically determine severity based on context"""
        if action_type == 'delete':
            return 'high'
        elif action_type in ['calculation', 'toggle']:
            return 'medium'
        elif object_model in ['drkds.cost.template', 'drkds.kit.component']:
            return 'medium'  # Template/component changes are more important
        else:
            return 'low'
    
    def _auto_determine_category(self, action_type, field_name):
        """Automatically determine category based on context"""
        if action_type == 'calculation':
            return 'calculation'
        elif field_name in ['current_rate', 'rate', 'rate_multiplier']:
            return 'data'
        elif action_type in ['create', 'update', 'delete']:
            return 'data'
        elif action_type == 'toggle':
            return 'user_action'
        else:
            return 'system'
    
    def _get_client_ip(self):
        """Get client IP address"""
        if request:
            return request.httprequest.environ.get('REMOTE_ADDR', 'Unknown')
        return 'Unknown'
    
    def _get_user_agent(self):
        """Get user agent string"""
        if request:
            return request.httprequest.environ.get('HTTP_USER_AGENT', 'Unknown')
        return 'Unknown'
    
    def _get_session_id(self):
        """Get session ID"""
        if request and hasattr(request, 'session'):
            return request.session.sid
        return 'Unknown'
    
    @api.model
    def cleanup_old_logs(self, days=90):
        """Clean up logs older than specified days"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([('create_date', '<', cutoff_date)])
        count = len(old_logs)
        old_logs.unlink()
        return count
    
    def action_view_related_object(self):
        """Action to view the related object if it exists"""
        self.ensure_one()
        if not self.object_model or not self.object_id:
            return False
        
        try:
            # Check if object still exists
            obj = self.env[self.object_model].browse(self.object_id)
            if not obj.exists():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Object Not Found'),
                        'message': _('The related object no longer exists.'),
                        'type': 'warning',
                    }
                }
            
            # Return action to view the object
            return {
                'name': _('Related Object'),
                'view_mode': 'form',
                'res_model': self.object_model,
                'res_id': self.object_id,
                'type': 'ir.actions.act_window',
            }
        except Exception:
            return False
    
    # Security: Only admin users can delete logs
    def unlink(self):
        """Override unlink to restrict deletion"""
        if not self.env.user.has_group('drkds_kit_calculations.group_admin'):
            raise ValidationError(_("Only administrators can delete change logs."))
        return super().unlink()
    
    # Methods for statistics and reporting
    @api.model
    def get_user_activity_stats(self, days=30):
        """Get user activity statistics"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        
        # Query for user activity
        query = """
            SELECT 
                u.name as user_name,
                l.action_type,
                COUNT(*) as count
            FROM drkds_change_log l
            JOIN res_users u ON l.user_id = u.id
            WHERE l.create_date >= %s
            GROUP BY u.name, l.action_type
            ORDER BY u.name, count DESC
        """
        
        self.env.cr.execute(query, (cutoff_date,))
        return self.env.cr.dictfetchall()
    
    @api.model
    def get_model_activity_stats(self, days=30):
        """Get model activity statistics"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        
        logs = self.search([
            ('create_date', '>=', cutoff_date),
            ('object_model', '!=', False)
        ])
        
        stats = {}
        for log in logs:
            model = log.object_model
            action = log.action_type
            if model not in stats:
                stats[model] = {}
            if action not in stats[model]:
                stats[model][action] = 0
            stats[model][action] += 1
        
        return stats