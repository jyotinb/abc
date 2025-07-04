# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Greenhouse-specific fields
    greenhouse_type = fields.Selection([
        ('hobby', 'Hobby Gardener'),
        ('commercial', 'Commercial Grower'),
        ('nursery', 'Plant Nursery'),
        ('retailer', 'Garden Center'),
        ('supplier', 'Equipment Supplier'),
    ], string='Greenhouse Type')
    
    growing_interests = fields.Many2many('greenhouse.symbol.library', 
                                       domain=[('category', 'in', ['plants', 'vegetables'])],
                                       string='Growing Interests')
    
    # Email preferences
    email_frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('seasonal', 'Seasonal'),
    ], default='monthly', string='Email Frequency')
    
    # Compliance
    unsubscribe_token = fields.Char('Unsubscribe Token', default=lambda self: self._generate_token())
    
    def _generate_token(self):
        import secrets
        return secrets.token_urlsafe(32)
