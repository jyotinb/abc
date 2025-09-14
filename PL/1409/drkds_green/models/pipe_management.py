from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PipeType(models.Model):
    _name = 'pipe.type'
    _description = 'Pipe Type Master'
    _order = 'name'
    
    name = fields.Char('Pipe Type', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)


class PipeSize(models.Model):
    _name = 'pipe.size'
    _description = 'Pipe Size Master'
    _order = 'size_in_mm'
    
    name = fields.Char('Size Name', required=True, help="Display name (e.g., 25mm, 25x25mm)")
    size_in_mm = fields.Float('Size (mm)', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)


class PipeWallThickness(models.Model):
    _name = 'pipe.wall_thickness'
    _description = 'Pipe Wall Thickness Master'
    _order = 'thickness_in_mm'
    
    name = fields.Char('Thickness Name', required=True, help="Display name (e.g., 2.0mm)")
    thickness_in_mm = fields.Float('Thickness (mm)', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)


class PipeManagement(models.Model):
    _name = 'pipe.management'
    _description = 'Pipe Management'
    _order = 'pipe_type, pipe_size, wall_thickness'
    
    name = fields.Char('Pipe Name', compute='_compute_name', store=True)
    pipe_type = fields.Many2one('pipe.type', string='Pipe Type', required=True)
    pipe_size = fields.Many2one('pipe.size', string='Pipe Size', required=True)
    wall_thickness = fields.Many2one('pipe.wall_thickness', string='Wall Thickness', required=True)
    
    # Specifications
    weight_per_unit = fields.Float('Weight per Unit (kg/m)', required=True, default=0.0)
    rate_per_kg = fields.Float('Rate per Kg', required=True, default=0.0)
    
    # Additional Info
    description = fields.Text('Description')
    notes = fields.Text('Notes')
    active = fields.Boolean('Active', default=True)
    
    @api.depends('pipe_type', 'pipe_size', 'wall_thickness')
    def _compute_name(self):
        for record in self:
            if record.pipe_type and record.pipe_size and record.wall_thickness:
                record.name = f"{record.pipe_type.name} - {record.pipe_size.name} - {record.wall_thickness.name}"
            else:
                record.name = "Incomplete Pipe Configuration"
    
    @api.constrains('weight_per_unit', 'rate_per_kg')
    def _check_positive_values(self):
        for record in self:
            if record.weight_per_unit < 0:
                raise ValidationError('Weight per unit cannot be negative.')
            if record.rate_per_kg < 0:
                raise ValidationError('Rate per kg cannot be negative.')
    
    _sql_constraints = [
        ('unique_pipe_combination', 
         'unique(pipe_type, pipe_size, wall_thickness)', 
         'A pipe with this type, size, and wall thickness already exists.')
    ]
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.pipe_type.name} {record.pipe_size.name} {record.wall_thickness.name}"
            result.append((record.id, name))
        return result