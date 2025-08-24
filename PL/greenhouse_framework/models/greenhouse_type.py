# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json

class GreenhouseType(models.Model):
    """Greenhouse types like NVPH, Tunnel, Fan&Pad"""
    _name = 'greenhouse.type'
    _description = 'Greenhouse Type Template'
    _order = 'sequence, name'
    
    name = fields.Char('Type Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    
    # Visual
    icon = fields.Char('Icon', default='fa-home', help='Font Awesome icon class')
    color = fields.Integer('Color', default=1, help='Color index for UI')
    image = fields.Binary('Image', help='Image for type selection')
    
    # Sections configuration
    section_ids = fields.Many2many(
        'greenhouse.section.template',
        'greenhouse_type_section_rel',
        'type_id',
        'section_id',
        string='Available Sections'
    )
    
    # Default inputs configuration (JSON)
    default_inputs = fields.Text(
        'Default Input Values',
        help='JSON configuration for default input values'
    )
    
    # Quick info for users
    typical_size = fields.Char('Typical Size', help='e.g., 500-2000 sqm')
    typical_use = fields.Char('Typical Use', help='e.g., Vegetables, Flowers')
    
    @api.model
    def get_default_inputs(self):
        """Return default inputs as dictionary"""
        if self.default_inputs:
            return json.loads(self.default_inputs)
        return {}
