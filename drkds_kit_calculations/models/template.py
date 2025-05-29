from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CostSheetTemplate(models.Model):
    _name = 'drkds.cost.template'
    _description = 'Cost Sheet Template'
    _order = 'name'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(string='Template Name', required=True)
    code = fields.Char(string='Template Code', required=True)
    description = fields.Text(string='Description')
    
    # Template Type
    template_type = fields.Selection([
        ('nvph_8x4', 'NVPH 8x4'),
        ('nvph_9x4', 'NVPH 9.6x4'),
        ('rack_pinion', 'Rack and Pinion'),
        ('custom', 'Custom')
    ], string='Template Type', required=True, default='custom')
    
    # Template Configuration
    component_line_ids = fields.One2many('drkds.template.component', 'template_id', 
                                       string='Components')
    parameter_line_ids = fields.One2many('drkds.template.parameter', 'template_id',
                                       string='Parameters')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    # Computed Fields
    component_count = fields.Integer(string='Components', compute='_compute_counts')
    parameter_count = fields.Integer(string='Parameters', compute='_compute_counts')
    cost_sheet_count = fields.Integer(string='Cost Sheets', compute='_compute_counts')
    
    @api.depends('component_line_ids', 'parameter_line_ids')
    def _compute_counts(self):
        for record in self:
            record.component_count = len(record.component_line_ids)
            record.parameter_count = len(record.parameter_line_ids)
            record.cost_sheet_count = self.env['drkds.cost.sheet'].search_count([
                ('template_id', '=', record.id)
            ])
    
    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Template code must be unique."))
    
    def action_view_cost_sheets(self):
        """Action to view cost sheets using this template"""
        return {
            'name': _('Cost Sheets'),
            'view_mode': 'tree,form',
            'res_model': 'drkds.cost.sheet',
            'type': 'ir.actions.act_window',
            'domain': [('template_id', '=', self.id)],
            'context': {'default_template_id': self.id}
        }
    
    def copy_template(self):
        """Create a copy of the template"""
        new_template = self.copy({
            'name': f"{self.name} (Copy)",
            'code': f"{self.code}_copy"
        })
        
        # Log the action
        self.env['drkds.change.log'].log_change(
            action_type='create',
            object_model=self._name,
            object_id=new_template.id,
            object_name=new_template.name,
            description=f'Template copied from "{self.name}"'
        )
        
        return {
            'name': _('Template Copy'),
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': new_template.id,
            'type': 'ir.actions.act_window',
        }
    
    @api.model
    def create(self, vals):
        result = super().create(vals)
        self.env['drkds.change.log'].log_change(
            action_type='create',
            object_model=self._name,
            object_id=result.id,
            object_name=result.name,
            description=f'Template "{result.name}" created'
        )
        return result
    
    def write(self, vals):
        for record in self:
            old_name = record.name
        
        result = super().write(vals)
        
        for record in self:
            self.env['drkds.change.log'].log_change(
                action_type='update',
                object_model=self._name,
                object_id=record.id,
                object_name=record.name,
                description=f'Template "{old_name}" updated'
            )
        return result