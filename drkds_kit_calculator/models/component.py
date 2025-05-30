# File: drkds_kit_calculator/models/component.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KitComponent(models.Model):
    _name = 'kit.component'
    _description = 'Kit Component'
    _order = 'category, name'
    
    name = fields.Char(string='Component Name', required=True)
    code = fields.Char(string='Code')
    category = fields.Selection([
        ('gi_pipes', 'GI Pipes & Structures'),
        ('aluminum', 'Aluminum Pipes'),
        ('hardware', 'Hardware & Clamps'),
        ('wire_rope', 'Wire & Rope'),
        ('pulleys', 'Pulleys & Mechanisms'),
        ('nets', 'Nets & Fabrics'),
        ('fasteners', 'Fasteners & Accessories'),
    ], string='Category', required=True)
    
    uom = fields.Selection([
        ('meter', 'Meter'),
        ('piece', 'Piece'),
        ('kg', 'Kilogram'),
        ('sqm', 'Square Meter'),
    ], string='Unit of Measure', required=True, default='piece')
    
    current_rate = fields.Float(string='Current Rate (₹)', required=True, digits=(12, 2))
    rate_multiplier = fields.Float(string='Rate Multiplier', default=1.2, digits=(12, 2))
    weight_per_unit = fields.Float(string='Weight per Unit (kg)', digits=(12, 3))
    standard_length = fields.Float(string='Standard Length (m)', digits=(12, 2))
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    
    # Computed fields
    rate_with_multiplier = fields.Float(string='Rate with Multiplier', 
                                       compute='_compute_rate_with_multiplier', 
                                       digits=(12, 2))
    
    @api.depends('current_rate', 'rate_multiplier')
    def _compute_rate_with_multiplier(self):
        for record in self:
            record.rate_with_multiplier = record.current_rate * record.rate_multiplier
    
    @api.constrains('current_rate')
    def _check_current_rate(self):
        for record in self:
            if record.current_rate <= 0:
                raise ValidationError(_("Rate must be greater than zero."))
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            result.append((record.id, name))
        return result