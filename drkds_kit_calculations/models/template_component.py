from odoo import models, fields, api, _

class TemplateComponent(models.Model):
    _name = 'drkds.template.component'
    _description = 'Template Component Line'
    _order = 'template_id, sequence, component_id'
    
    # Relations
    template_id = fields.Many2one('drkds.cost.template', string='Template', 
                                required=True, ondelete='cascade')
    component_id = fields.Many2one('drkds.kit.component', string='Component', 
                                 required=True)
    
    # Configuration
    sequence = fields.Integer(string='Sequence', default=10)
    default_enabled = fields.Boolean(string='Enabled by Default', default=True)
    is_mandatory = fields.Boolean(string='Mandatory Component', default=False,
                                help="Mandatory components cannot be disabled by users")
    
    # Formula Configuration
    quantity_formula = fields.Text(string='Quantity Formula',
                                 help="Formula to calculate quantity (e.g., 'length_8m * 6')")
    rate_formula = fields.Text(string='Rate Formula',
                             help="Formula to calculate rate (leave empty to use component rate)")
    length_formula = fields.Text(string='Length Formula',
                               help="Formula to calculate length in meters")
    
    # Helper Fields (Related)
    component_name = fields.Char(related='component_id.name', string='Component Name', store=True)
    component_code = fields.Char(related='component_id.code', string='Component Code')
    component_uom = fields.Char(related='component_id.uom_id.name', string='UOM')
    current_rate = fields.Float(related='component_id.current_rate', string='Current Rate')
    component_category = fields.Char(related='component_id.category_id.name', string='Category')
    
    # Formula Validation
    formula_valid = fields.Boolean(string='Formula Valid', compute='_compute_formula_valid')
    
    @api.depends('quantity_formula', 'rate_formula', 'length_formula')
    def _compute_formula_valid(self):
        """Basic formula validation"""
        for record in self:
            try:
                # Basic syntax check for formulas
                if record.quantity_formula:
                    compile(record.quantity_formula, '<string>', 'eval')
                if record.rate_formula:
                    compile(record.rate_formula, '<string>', 'eval')
                if record.length_formula:
                    compile(record.length_formula, '<string>', 'eval')
                record.formula_valid = True
            except:
                record.formula_valid = False
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.component_name} ({record.template_id.name})"
            result.append((record.id, name))
        return result
    
    @api.onchange('component_id')
    def _onchange_component_id(self):
        """Set default formulas based on component type"""
        if self.component_id:
            # Set some intelligent defaults based on component category
            category = self.component_id.category_id.name if self.component_id.category_id else ""
            
            if 'pipe' in category.lower():
                self.quantity_formula = "length_total"
                self.length_formula = "length_total"
            elif 'clamp' in category.lower() or 'joiner' in category.lower():
                self.quantity_formula = "no_of_joints"
            elif 'wire' in category.lower():
                self.quantity_formula = "wire_length_total"