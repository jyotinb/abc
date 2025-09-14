from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ComponentLine(models.Model):
    _name = 'component.line'
    _description = 'Component Line'
    _order = 'section, sequence, name'
    
    green_master_id = fields.Many2one('green.master', string='Greenhouse Project', required=True, ondelete='cascade')
    section = fields.Selection([
        ('asc', 'ASC Components'),
        ('frame', 'Frame Components'), 
        ('truss', 'Truss Components'),
        ('side_screen', 'Side Screen Components'),
        ('lower', 'Lower Section Components'),
    ], string='Section', required=True)
    sequence = fields.Integer('Sequence', default=10)
    
    name = fields.Char('Component Name', required=True)
    description = fields.Text('Description')
    required = fields.Boolean('Required', default=True)
    notes = fields.Text('Notes')
    
    # Quantity and Length
    nos = fields.Integer('Nos', default=1)
    length = fields.Float('Length (m)', default=0.0)
    
    # Length Configuration
    use_length_master = fields.Boolean('Use Length Master', default=False)
    length_master_id = fields.Many2one('length.master', string='Length Master')
    custom_length = fields.Float('Custom Length (m)', default=0.0)
    
    # Computed Length Fields
    total_length = fields.Float('Total Length (m)', compute='_compute_totals', store=True)
    
    # Pipe Selection
    pipe_id = fields.Many2one('pipe.management', string='Pipe Selection')
    
    # Pipe Details (computed from pipe selection)
    pipe_type = fields.Char('Pipe Type', compute='_compute_pipe_details', store=True)
    pipe_size = fields.Char('Size (mm)', compute='_compute_pipe_details', store=True)
    wall_thickness = fields.Char('WT (mm)', compute='_compute_pipe_details', store=True)
    weight_per_unit = fields.Float('Weight/Unit (kg/m)', compute='_compute_pipe_details', store=True)
    rate_per_kg = fields.Float('Rate/Kg', compute='_compute_pipe_details', store=True)
    
    # Cost Calculations
    total_weight = fields.Float('Total Weight (kg)', compute='_compute_totals', store=True)
    total_cost = fields.Float('Total Cost', compute='_compute_totals', store=True)
    
    # Status
    is_calculated = fields.Boolean('Is Calculated', default=False, help="True if auto-calculated by system")
    
    @api.depends('pipe_id')
    def _compute_pipe_details(self):
        for record in self:
            if record.pipe_id:
                record.pipe_type = record.pipe_id.pipe_type.name if record.pipe_id.pipe_type else ''
                record.pipe_size = f"{record.pipe_id.pipe_size.name}" if record.pipe_id.pipe_size else ''
                record.wall_thickness = f"{record.pipe_id.wall_thickness.name}" if record.pipe_id.wall_thickness else ''
                record.weight_per_unit = record.pipe_id.weight_per_unit or 0.0
                record.rate_per_kg = record.pipe_id.rate_per_kg or 0.0
            else:
                record.pipe_type = ''
                record.pipe_size = ''
                record.wall_thickness = ''
                record.weight_per_unit = 0.0
                record.rate_per_kg = 0.0
    
    @api.depends('nos', 'length', 'weight_per_unit', 'rate_per_kg')
    def _compute_totals(self):
        for record in self:
            record.total_length = record.nos * record.length
            record.total_weight = record.total_length * record.weight_per_unit
            record.total_cost = record.total_weight * record.rate_per_kg
    
    @api.onchange('use_length_master', 'length_master_id', 'custom_length')
    def _onchange_length_configuration(self):
        """Handle length configuration changes"""
        if self.use_length_master and self.length_master_id:
            self.length = self.length_master_id.length_value
        elif not self.use_length_master and self.custom_length > 0:
            self.length = self.custom_length
    
    @api.constrains('nos', 'length', 'custom_length')
    def _check_positive_values(self):
        for record in self:
            if record.nos < 0:
                raise ValidationError('Number of components cannot be negative.')
            if record.length < 0:
                raise ValidationError('Length cannot be negative.')
            if record.custom_length < 0:
                raise ValidationError('Custom length cannot be negative.')
    
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.section.upper()}] {record.name}"
            if record.pipe_id:
                name += f" - {record.pipe_type} {record.pipe_size}"
            result.append((record.id, name))
        return result