# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class DrainagePipeOption(models.Model):
    """Drainage Pipe Length Options with Pricing"""
    _name = 'drainage.pipe.option'
    _description = 'Drainage Pipe Length Options'
    _order = 'length_value asc'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    length_value = fields.Float(string='Length (m)', required=True, tracking=True)
    unit_price = fields.Float(string='Price per Unit', default=0.0, tracking=True,
                              help="Price per pipe unit")
    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('length_value')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.length_value}m" if record.length_value else "0.0m"
    
    def name_get(self):
        result = []
        for record in self:
            price_info = f" - ₹{record.unit_price}/unit" if record.unit_price > 0 else ""
            name = f"{record.length_value}m{price_info}" if record.length_value else "0.0m"
            result.append((record.id, name))
        return result
    
    _sql_constraints = [
        ('unique_drainage_pipe_length', 'unique(length_value)', 
         'A drainage pipe option with this length already exists.')
    ]


class DoorModel(models.Model):
    """Door Model Master for Sliding Doors"""
    _name = 'door.model'
    _description = 'Door Model Master'
    _order = 'sequence, name'
    
    name = fields.Char(string='Door Model Name', required=True, tracking=True)
    code = fields.Char(string='Model Code', tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    unit_price = fields.Float(string='Price per Door', default=0.0, tracking=True,
                              help="Price per door unit")
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    notes = fields.Text(string='Notes')
    
    # Specifications
    door_width = fields.Float(string='Door Width (m)', tracking=True)
    door_height = fields.Float(string='Door Height (m)', tracking=True)
    material = fields.Char(string='Material', tracking=True)
    
    def name_get(self):
        result = []
        for record in self:
            price_info = f" - ₹{record.unit_price}" if record.unit_price > 0 else ""
            name = f"{record.name}{price_info}"
            if record.code:
                name = f"[{record.code}] {name}"
            result.append((record.id, name))
        return result
    
    _sql_constraints = [
        ('unique_door_model_name', 'unique(name)', 
         'A door model with this name already exists.'),
        ('unique_door_model_code', 'unique(code)', 
         'A door model with this code already exists.')
    ]
