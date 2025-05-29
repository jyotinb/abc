from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ComponentCategory(models.Model):
    _name = 'drkds.component.category'
    _description = 'Component Category'
    _order = 'name'
    
    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    component_count = fields.Integer(string='Components', compute='_compute_component_count')
    
    @api.depends('name')
    def _compute_component_count(self):
        for record in self:
            record.component_count = self.env['drkds.kit.component'].search_count([
                ('category_id', '=', record.id)
            ])

class KitComponent(models.Model):
    _name = 'drkds.kit.component'
    _description = 'Kit Component Master'
    _order = 'category_id, name'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(string='Component Name', required=True)
    code = fields.Char(string='Component Code')
    category_id = fields.Many2one('drkds.component.category', string='Category', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Pricing
    current_rate = fields.Float(string='Current Rate', digits=(12, 2), required=True)
    rate_multiplier = fields.Float(string='Rate Multiplier', default=1.0,
                                  help="Multiplier for rate calculations (e.g., 1.2 for 20% markup)")
    
    # Physical Properties
    weight_per_unit = fields.Float(string='Weight per Unit', digits=(12, 3))
    standard_length = fields.Float(string='Standard Length', digits=(12, 3),
                                  help="Standard length for pipes/rods")
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    # Template Usage
    template_count = fields.Integer(string='Used in Templates', compute='_compute_template_count')
    
    @api.depends('name')
    def _compute_template_count(self):
        for record in self:
            record.template_count = self.env['drkds.template.component'].search_count([
                ('component_id', '=', record.id)
            ])
    
    @api.constrains('current_rate')
    def _check_current_rate(self):
        for record in self:
            if record.current_rate <= 0:
                raise ValidationError(_("Current rate must be greater than zero."))
    
    @api.constrains('rate_multiplier')
    def _check_rate_multiplier(self):
        for record in self:
            if record.rate_multiplier <= 0:
                raise ValidationError(_("Rate multiplier must be greater than zero."))
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            result.append((record.id, name))
        return result
    
    @api.model
    def create(self, vals):
        result = super().create(vals)
        self.env['drkds.change.log'].log_change(
            action_type='create',
            object_model=self._name,
            object_id=result.id,
            object_name=result.name,
            description=f'Component "{result.name}" created'
        )
        return result
    
    def write(self, vals):
        for record in self:
            old_values = {}
            for field in vals:
                if hasattr(record, field):
                    old_values[field] = getattr(record, field)
        
        result = super().write(vals)
        
        for record in self:
            for field, new_value in vals.items():
                if field in old_values:
                    self.env['drkds.change.log'].log_change(
                        action_type='update',
                        object_model=self._name,
                        object_id=record.id,
                        object_name=record.name,
                        field_name=field,
                        old_value=old_values[field],
                        new_value=new_value,
                        description=f'Component "{record.name}" updated'
                    )
        return result