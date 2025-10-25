# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccessoriesComponentLine(models.Model):
    _name = 'accessories.component.line'
    _description = 'Accessories Component Line'
    _order = 'section, sequence, name'
    
    # Relationships
    green_master_id = fields.Many2one('green.master', string='Green Master', 
                                     ondelete='cascade', required=True)
    accessories_master_id = fields.Many2one('accessories.master', string='Accessory Type',
                                           tracking=True)
    
    # Basic Information
    sequence = fields.Integer('Sequence', default=10, tracking=True)
    section = fields.Selection([
        ('profiles', 'Profiles'),
        ('brackets', 'Brackets'),
        ('wires_connectors', 'Wires & Connectors'),
        ('clamps', 'Clamps'),
        ('foundation', 'Foundation')
    ], string='Section', required=True, tracking=True)
    
    name = fields.Char('Component Name', required=True, tracking=True)
    description = fields.Text('Description', tracking=True)
    
    # Quantities and Specifications
    nos = fields.Integer('Quantity/Rolls', default=0, tracking=True, 
                        help="For covering: Number of rolls")
    length = fields.Float('Length (m)', default=0.0, tracking=True,
                         help="For covering: Length per roll")
    width = fields.Float('Width (m)', default=0.0, tracking=True,
                        help="For covering: Width of material")
    quantity = fields.Float('Quantity (m²)', default=0.0, tracking=True,
                           help="For covering: Total square meters (Width × Length × Rolls)")
    size_specification = fields.Char('Size/Type Specification', tracking=True)
    unit_price = fields.Float('Unit Price', default=0.0, tracking=True,
                             help="For covering: Price per square meter")
    
    # Calculations
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    
    # System fields
    is_calculated = fields.Boolean('Auto Calculated', default=False, tracking=True)
    notes = fields.Text('Notes', tracking=True)
    
    @api.depends('nos', 'unit_price', 'quantity')
    def _compute_total_cost(self):
        for record in self:
            # For covering materials, use quantity (sq meters) × unit_price
            # For other accessories, use nos × unit_price
            if record.quantity > 0:
                record.total_cost = record.quantity * record.unit_price
            else:
                record.total_cost = record.nos * record.unit_price
    
    @api.onchange('accessories_master_id')
    def _onchange_accessories_master_id(self):
        if self.accessories_master_id:
            self.name = self.accessories_master_id.name
            self.section = self.accessories_master_id.category
            self.unit_price = self.accessories_master_id.unit_price
            self.size_specification = self.accessories_master_id.size_specification
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.size_specification:
                name = f"{name} ({record.size_specification})"
            if record.section:
                try:
                    section_name = dict(record._fields['section'].selection)[record.section]
                    name = f"[{section_name}] {name}"
                except (KeyError, AttributeError):
                    pass
            result.append((record.id, name))
        return result
