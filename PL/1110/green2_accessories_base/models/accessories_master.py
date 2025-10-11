# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccessoriesMaster(models.Model):
    _name = 'accessories.master'
    _description = 'Accessories Master Data'
    _order = 'category, sequence, name'
    
    name = fields.Char('Accessory Name', required=True, tracking=True)
    category = fields.Selection([
        ('brackets', 'Brackets'),
        ('wires_connectors', 'Wires & Connectors'),
        ('clamps', 'Clamps'),
        ('profiles', 'Profiles'),
        ('foundation', 'Foundation'),
    ], string='Category', required=True, tracking=True)
    
    sequence = fields.Integer('Sequence', default=10, tracking=True)
    unit_price = fields.Float('Unit Price', default=0.0, tracking=True)
    size_specification = fields.Char('Size/Type Specification', tracking=True)
    
    active = fields.Boolean('Active', default=True, tracking=True)
    notes = fields.Text('Notes', tracking=True)
    
    # Display and search
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('name', 'size_specification', 'category')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.size_specification:
                name = f"{name} ({record.size_specification})"
            if record.category:
                category_name = dict(record._fields['category'].selection)[record.category]
                name = f"[{category_name}] {name}"
            record.display_name = name
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result
    
    _sql_constraints = [
        ('unique_accessory_size', 
         'unique(name, size_specification, category)', 
         'An accessory with this name, size, and category already exists.')
    ]
