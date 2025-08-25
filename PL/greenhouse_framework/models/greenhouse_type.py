# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json
import logging

_logger = logging.getLogger(__name__)


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
    
    # Statistics
    project_count = fields.Integer('Project Count', compute='_compute_project_count')
    
    @api.depends('name')
    def _compute_project_count(self):
        """Count projects using this type"""
        for record in self:
            record.project_count = self.env['greenhouse.project'].search_count([
                ('greenhouse_type_id', '=', record.id)
            ])
    
    @api.model
    def get_default_inputs(self):
        """Return default inputs as dictionary"""
        self.ensure_one()
        if self.default_inputs:
            try:
                return json.loads(self.default_inputs)
            except json.JSONDecodeError as e:
                _logger.error(f"Invalid JSON in default_inputs for type {self.name}: {str(e)}")
                return {}
        return {}
    
    def action_view_projects(self):
        """View projects using this type"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Projects - {self.name}',
            'res_model': 'greenhouse.project',
            'view_mode': 'tree,form',
            'domain': [('greenhouse_type_id', '=', self.id)],
            'context': {'default_greenhouse_type_id': self.id},
        }
    
    def action_duplicate_type(self):
        """Duplicate this greenhouse type with a new name"""
        self.ensure_one()
        new_type = self.copy({
            'name': f"{self.name} (Copy)",
            'code': f"{self.code}_copy",
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'greenhouse.type',
            'res_id': new_type.id,
            'view_mode': 'form',
        }
    
    @api.model
    def create_sample_types(self):
        """Create sample greenhouse types for testing"""
        sample_types = [
            {
                'name': 'Basic Polyhouse',
                'code': 'basic',
                'description': 'Simple structure for beginners',
                'typical_size': '200-500 sqm',
                'typical_use': 'Leafy Vegetables',
                'icon': 'fa-leaf',
                'color': 2,
            },
            {
                'name': 'Advanced NVPH',
                'code': 'advanced_nvph',
                'description': 'Professional naturally ventilated polyhouse',
                'typical_size': '1000-5000 sqm',
                'typical_use': 'Commercial Farming',
                'icon': 'fa-building',
                'color': 3,
            },
        ]
        
        for type_data in sample_types:
            existing = self.search([('code', '=', type_data['code'])], limit=1)
            if not existing:
                self.create(type_data)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Sample greenhouse types created',
                'type': 'success',
            }
        }