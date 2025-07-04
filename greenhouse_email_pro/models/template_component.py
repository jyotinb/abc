# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TemplateComponent(models.Model):
    _name = 'email.template.component'
    _description = 'Email Template Component'
    _order = 'sequence'

    name = fields.Char('Component Name', required=True)
    component_type = fields.Selection([
        ('header', 'Header'),
        ('hero', 'Hero Section'),
        ('text', 'Text Block'),
        ('image', 'Image Block'),
        ('button', 'Button'),
        ('two_column', 'Two Columns'),
        ('footer', 'Footer'),
    ], string='Type', required=True)
    
    html_content = fields.Text('HTML Content', required=True)
    sequence = fields.Integer('Sequence', default=10)
    
    def get_rendered_html(self, variables=None):
        """Render HTML with variables"""
        html = self.html_content
        if variables:
            for key, value in variables.items():
                html = html.replace(f'{{{{{key}}}}}', str(value))
        return html
