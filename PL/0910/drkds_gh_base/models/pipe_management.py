from odoo import models, fields, api

class PipeType(models.Model):
    _name = 'greenhouse.pipe.type'
    _description = 'Pipe Type'
    
    name = fields.Char('Name', required=True)

class PipeSize(models.Model):
    _name = 'greenhouse.pipe.size'
    _description = 'Pipe Size'
    
    name = fields.Char('Name', required=True)
    size_mm = fields.Float('Size (mm)', required=True)

class PipeWallThickness(models.Model):
    _name = 'greenhouse.pipe.wall.thickness'
    _description = 'Wall Thickness'
    
    name = fields.Char('Name', required=True)
    thickness_mm = fields.Float('Thickness (mm)', required=True)

class PipeManagement(models.Model):
    _name = 'greenhouse.pipe.management'
    _description = 'Pipe Management'
    _rec_name = 'display_name'
    
    pipe_type_id = fields.Many2one('greenhouse.pipe.type', 'Type', required=True)
    pipe_size_id = fields.Many2one('greenhouse.pipe.size', 'Size', required=True)
    wall_thickness_id = fields.Many2one('greenhouse.pipe.wall.thickness', 'Wall Thickness', required=True)
    weight = fields.Float('Weight (kg/m)', required=True)
    rate = fields.Float('Rate (per kg)', required=True)
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('pipe_type_id', 'pipe_size_id', 'wall_thickness_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.pipe_type_id and rec.pipe_size_id and rec.wall_thickness_id:
                rec.display_name = f"{rec.pipe_type_id.name} {rec.pipe_size_id.size_mm}mm x {rec.wall_thickness_id.thickness_mm}mm"
            else:
                rec.display_name = "New Pipe"
    
    _sql_constraints = [
        ('unique_pipe', 'unique(pipe_type_id, pipe_size_id, wall_thickness_id)', 'This pipe combination already exists!')
    ]
