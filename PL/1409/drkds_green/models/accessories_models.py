from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccessoriesMaster(models.Model):
    _name = 'accessories.master'
    _description = 'Accessories Master'
    _order = 'category, name'
    
    name = fields.Char('Accessory Name', required=True)
    category = fields.Selection([
        ('brackets', 'Brackets'),
        ('wires_connectors', 'Wires & Connectors'),
        ('clamps', 'Clamps'),
        ('profiles', 'Profiles'), 
        ('foundation', 'Foundation'), 
    ], string='Category', required=True)
    size_specification = fields.Char('Size/Specification', required=True)
    unit_price = fields.Float('Unit Price', default=0.0)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('unique_accessory_size', 
         'unique(name, size_specification, category)', 
         'An accessory with this name, size, and category already exists.')
    ]
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({record.size_specification})"
            result.append((record.id, name))
        return result


class AccessoriesComponentLine(models.Model):
    _name = 'accessories.component.line'
    _description = 'Accessories Component Line'
    _order = 'section, sequence, name'
    
    green_master_id = fields.Many2one('green.master', string='Greenhouse Project', required=True, ondelete='cascade')
    section = fields.Selection([
        ('profiles', 'Profiles'),  
        ('brackets', 'Brackets'),
        ('wires_connectors', 'Wires & Connectors'),
        ('clamps', 'Clamps'),
        ('foundation', 'Foundation')
    ], string='Section', required=True)
    sequence = fields.Integer('Sequence', default=10)
    
    name = fields.Char('Component Name', required=True)
    description = fields.Text('Description')
    
    # Quantity and Pricing
    nos = fields.Integer('Quantity', default=1)
    size_specification = fields.Char('Size/Type')
    unit_price = fields.Float('Unit Price', default=0.0)
    
    # Size Management
    auto_detected_size = fields.Char('Auto-Detected Size', readonly=True, 
                                   help="Size automatically detected by system (e.g., from pipe sizes)")
    size_override = fields.Boolean('Override Size', default=False, 
                                 help="Enable to manually override the size specification")
    manual_size = fields.Char('Manual Size', 
                            help="Manually entered size when override is enabled")
    
    # Master Data Link
    accessories_master_id = fields.Many2one('accessories.master', string='Master Data')
    
    # Cost Calculation
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)
    
    # Status
    is_calculated = fields.Boolean('Is Calculated', default=False, help="True if auto-calculated by system")
    notes = fields.Text('Notes')
    
    @api.depends('nos', 'unit_price')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.nos * record.unit_price
    
    @api.onchange('accessories_master_id')
    def _onchange_accessories_master_id(self):
        """Handle accessories master changes"""
        if self.accessories_master_id:
            self.name = self.accessories_master_id.name
            self.section = self.accessories_master_id.category
            self.unit_price = self.accessories_master_id.unit_price
            if not self.size_override:
                self.size_specification = self.accessories_master_id.size_specification
    
    @api.onchange('size_override', 'manual_size')
    def _onchange_size_override(self):
        """Handle size override changes"""
        if self.size_override and self.manual_size:
            self.size_specification = self.manual_size
        elif not self.size_override and self.auto_detected_size:
            self.size_specification = self.auto_detected_size
    
    @api.constrains('nos', 'unit_price')
    def _check_positive_values(self):
        for record in self:
            if record.nos < 0:
                raise ValidationError('Quantity cannot be negative.')
            if record.unit_price < 0:
                raise ValidationError('Unit price cannot be negative.')
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.section.upper()}] {record.name}"
            if record.size_specification:
                name += f" ({record.size_specification})"
            result.append((record.id, name))
        return result