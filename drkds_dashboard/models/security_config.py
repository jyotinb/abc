from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
import secrets
import hashlib
import logging

class DrkdsDashboardSecurityConfig(models.Model):
    _name = 'drkds.dashboard.security.config'
    _description = 'Dashboard Security Configuration'
    _rec_name = 'config_name'

    config_name = fields.Char(string='Configuration Name', required=True)
    
    security_level = fields.Selection([
        ('low', 'Low Security'),
        ('medium', 'Medium Security'),
        ('high', 'High Security'),
        ('critical', 'Critical Security')
    ], default='medium', required=True)

    # Password Policy
    min_password_length = fields.Integer(default=12, required=True)
    require_uppercase = fields.Boolean(default=True)
    require_lowercase = fields.Boolean(default=True)
    require_numbers = fields.Boolean(default=True)
    require_special_chars = fields.Boolean(default=True)

    # Access Control
    max_login_attempts = fields.Integer(default=5, required=True)
    lockout_duration = fields.Integer(default=30, required=True)  # minutes

    # Two-Factor Authentication - Simplified for Community
    enable_two_factor = fields.Boolean(default=False)
    two_factor_method = fields.Selection([
        ('email', 'Email Verification')
    ], default='email')

    @api.constrains('min_password_length', 'max_login_attempts', 'lockout_duration')
    def _validate_security_settings(self):
        for config in self:
            if config.min_password_length < 8:
                raise ValidationError("Minimum password length must be at least 8 characters")
            
            if config.max_login_attempts < 3 or config.max_login_attempts > 10:
                raise ValidationError("Login attempts must be between 3 and 10")
            
            if config.lockout_duration < 15 or config.lockout_duration > 240:
                raise ValidationError("Lockout duration must be between 15 and 240 minutes")

    def validate_password(self, password):
        """
        Validate password against configured complexity rules
        """
        if len(password) < self.min_password_length:
            return False

        checks = [
            (self.require_special_chars, r'[!@#$%^&*(),.?":{}|<>]', "Special characters"),
            (self.require_uppercase, r'[A-Z]', "Uppercase letters"),
            (self.require_lowercase, r'[a-z]', "Lowercase letters"),
            (self.require_numbers, r'\d', "Numbers")
        ]

        for enabled, pattern, description in checks:
            if enabled and not re.search(pattern, password):
                return False

        return True

    def generate_security_token(self, user_id=None):
        """
        Generate a cryptographically secure token
        """
        base_token = secrets.token_hex(32)
        user_context = user_id or self.env.user.id
        salted_token = f"{base_token}|{user_context}|{fields.Datetime.now()}"
        return hashlib.sha256(salted_token.encode()).hexdigest()

    @api.model
    def get_active_security_config(self):
        """
        Retrieve the active security configuration
        """
        config = self.search([], limit=1)
        return config or self.create({
            'config_name': 'Default Security Configuration',
            'security_level': 'medium'
        })

class DrkdsDashboardSecurityLog(models.Model):
    _name = 'drkds.dashboard.security.log'
    _description = 'Security Event Logs'
    _order = 'create_date desc'

    event_type = fields.Selection([
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('access_denied', 'Access Denied'),
        ('two_factor', 'Two-Factor Authentication')
    ], required=True)

    user_id = fields.Many2one('res.users', string='User', required=True)
    ip_address = fields.Char(string='IP Address')
    details = fields.Text(string='Event Details')

    @api.model
    def log_security_event(self, event_type, user=None, details=None, ip_address=None):
        """
        Log a security-related event
        """
        current_user = user or self.env.user
        return self.create({
            'event_type': event_type,
            'user_id': current_user.id,
            'details': details or '',
            'ip_address': ip_address or ''
        })
