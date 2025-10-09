from odoo import models, fields, api

class GreenhouseComponentLine(models.Model):
    _name = 'greenhouse.component.line'
    _description = 'Component Line'
    _order = 'section, sequence, name'
    
    project_id = fields.Many2one('greenhouse.project', 'Project', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    
    section = fields.Selection([
        ('frame', 'Frame'),
        ('truss', 'Truss'),
        ('lower', 'Lower'),
        ('asc', 'ASC'),
        ('side_screen', 'Side Screen'),
    ], string='Section', required=True)
    
    name = fields.Char('Component Name', required=True)
    description = fields.Text('Description')
    required = fields.Boolean('Required', default=True)
    
    nos = fields.Integer('Nos', default=0)
    length = fields.Float('Length (m)', default=0.0)
    
    use_length_master = fields.Boolean('Use Length Master', default=False)
    length_master_id = fields.Many2one('greenhouse.length.master', 'Length Master')
    custom_length = fields.Float('Custom Length', default=0.0)
    
    pipe_id = fields.Many2one('greenhouse.pipe.management', 'Pipe')
    pipe_type = fields.Char('Pipe Type', related='pipe_id.pipe_type_id.name', readonly=True)
    pipe_size = fields.Float('Size (mm)', related='pipe_id.pipe_size_id.size_mm', readonly=True)
    wall_thickness = fields.Float('WT (mm)', related='pipe_id.wall_thickness_id.thickness_mm', readonly=True)
    weight_per_unit = fields.Float('Weight/Unit', related='pipe_id.weight', readonly=True)
    rate_per_kg = fields.Float('Rate/Kg', related='pipe_id.rate', readonly=True)
    
    total_length = fields.Float('Total Length', compute='_compute_totals', store=True)
    total_weight = fields.Float('Total Weight', compute='_compute_totals', store=True)
    total_cost = fields.Float('Total Cost', compute='_compute_totals', store=True)
    
    is_calculated = fields.Boolean('Auto Calculated', default=False)
    notes = fields.Text('Notes')
    
    @api.depends('nos', 'length', 'weight_per_unit', 'rate_per_kg')
    def _compute_totals(self):
        for rec in self:
            rec.total_length = rec.nos * rec.length
            rec.total_weight = rec.total_length * (rec.weight_per_unit or 0)
            rec.total_cost = rec.total_weight * (rec.rate_per_kg or 0)
    
    @api.onchange('use_length_master', 'length_master_id', 'custom_length')
    def _onchange_length(self):
        if self.use_length_master and self.length_master_id:
            self.length = self.length_master_id.length_value
        elif not self.use_length_master and self.custom_length:
            self.length = self.custom_length
