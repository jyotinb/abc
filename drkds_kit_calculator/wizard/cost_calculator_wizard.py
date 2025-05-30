# File: drkds_kit_calculator/wizard/cost_calculator_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KitCostCalculatorWizard(models.TransientModel):
    _name = 'kit.cost.calculator.wizard'
    _description = 'Kit Cost Calculator Wizard'
    
    # Step 1: Template Selection
    template_id = fields.Many2one('kit.template', string='Template', required=True)
    template_description = fields.Text(related='template_id.description', readonly=True)
    
    # Step 2: Project Information
    project_name = fields.Char(string='Project Name')
    client_name = fields.Char(string='Client Name', required=True)
    site_location = fields.Char(string='Site Location')
    quotation_number = fields.Char(string='Quotation Number')
    
    # Step 3: Quick Parameters
    length_8m = fields.Float(string='Length at 8m Bay (m)', default=48.0)
    no_8m_bays = fields.Integer(string='Number of 8m Bays', default=6)
    length_4m = fields.Float(string='Length at 4m Span (m)', default=48.0)
    no_4m_spans = fields.Integer(string='Number of 4m Spans', default=12)
    grid_size_bay = fields.Float(string='Grid Size Bay (m)', default=8.0)
    grid_size_span = fields.Float(string='Grid Size Span (m)', default=4.0)
    corridor_length = fields.Float(string='Corridor Length (m)', default=50.0)
    
    # Computed
    total_area = fields.Float(string='Total Area (m²)', compute='_compute_total_area')
    estimated_cost = fields.Float(string='Estimated Cost (₹)', compute='_compute_estimated_cost')
    
    @api.depends('length_8m', 'no_8m_bays', 'length_4m', 'no_4m_spans', 'grid_size_bay', 'grid_size_span')
    def _compute_total_area(self):
        for record in self:
            area_8m = record.length_8m * record.no_8m_bays * record.grid_size_bay
            area_4m = record.length_4m * record.no_4m_spans * record.grid_size_span
            record.total_area = (area_8m + area_4m) / 1000  # Convert to proper scale
    
    @api.depends('template_id', 'total_area')
    def _compute_estimated_cost(self):
        for record in self:
            if record.template_id and record.total_area > 0:
                # Rough estimation based on template components
                avg_rate = 0
                if record.template_id.component_ids:
                    rates = [line.component_id.current_rate for line in record.template_id.component_ids]
                    avg_rate = sum(rates) / len(rates) if rates else 0
                record.estimated_cost = record.total_area * avg_rate * 0.5
            else:
                record.estimated_cost = 0.0
    
    def action_create_cost_sheet(self):
        self.ensure_one()
        
        if not self.template_id or not self.client_name:
            raise ValidationError(_("Template and Client Name are required."))
        
        # Create cost sheet
        cost_sheet = self.env['kit.cost.sheet'].create({
            'template_id': self.template_id.id,
            'project_name': self.project_name,
            'client_name': self.client_name,
            'site_location': self.site_location,
            'quotation_number': self.quotation_number,
        })
        
        # Set parameter values
        self._set_parameter_values(cost_sheet)
        
        return {
            'name': _('Cost Sheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'kit.cost.sheet',
            'res_id': cost_sheet.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _set_parameter_values(self, cost_sheet):
        param_mapping = {
            'length_8m': self.length_8m,
            'no_8m_bays': self.no_8m_bays,
            'length_4m': self.length_4m,
            'no_4m_spans': self.no_4m_spans,
            'grid_size_bay': self.grid_size_bay,
            'grid_size_span': self.grid_size_span,
            'corridor_length': self.corridor_length,
            'total_area': self.total_area,
        }
        
        for param_line in cost_sheet.parameter_ids:
            code = param_line.parameter_code
            if code in param_mapping:
                value = param_mapping[code]
                if param_line.parameter_type == 'float':
                    param_line.value_float = value
                elif param_line.parameter_type == 'integer':
                    param_line.value_integer = int(value)
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            # Set defaults based on template type
            if self.template_id.template_type == 'nvph_8x4':
                self.length_8m = 48.0
                self.no_8m_bays = 6
                self.grid_size_bay = 8.0
            elif self.template_id.template_type == 'nvph_9x4':
                self.length_8m = 57.6
                self.no_8m_bays = 6
                self.grid_size_bay = 9.6