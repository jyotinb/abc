from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CostSheetWizard(models.TransientModel):
    _name = 'drkds.cost.sheet.wizard'
    _description = 'Cost Sheet Creation Wizard'
    
    # Step 1: Template Selection
    template_id = fields.Many2one('drkds.cost.template', string='Template', required=True)
    template_description = fields.Text(related='template_id.description', string='Template Description', readonly=True)
    template_type = fields.Selection(related='template_id.template_type', readonly=True)
    
    # Step 2: Project Information
    client_id = fields.Many2one('res.partner', string='Client', required=True)
    quotation_number = fields.Char(string='Quotation Number')
    project_name = fields.Char(string='Project Name')
    site_location = fields.Char(string='Site Location')
    installation_position = fields.Selection([
        ('inside', 'Inside'),
        ('outside', 'Outside')
    ], string='Installation Position', default='inside')
    
    # Step 3: Quick Parameters (most common ones)
    length_8m = fields.Float(string='Length at 8m Bay', default=48.0)
    length_4m = fields.Float(string='Length at 4m Span', default=48.0)
    no_8m_bays = fields.Integer(string='Number of 8m Bays', default=6)
    no_4m_spans = fields.Integer(string='Number of 4m Spans', default=12)
    grid_size_bay = fields.Float(string='Grid Size (Bay)', default=8.0)
    grid_size_span = fields.Float(string='Grid Size (Span)', default=4.0)
    corridor_length = fields.Float(string='Length of Corridor', default=50.0)
    
    # Computed fields
    total_area = fields.Float(string='Total Area (m²)', compute='_compute_total_area', store=True)
    estimated_cost = fields.Float(string='Estimated Cost', compute='_compute_estimated_cost')
    
    # Wizard steps
    step = fields.Selection([
        ('template', 'Select Template'),
        ('project', 'Project Information'),
        ('parameters', 'Parameters'),
        ('summary', 'Summary & Create')
    ], string='Step', default='template')
    
    @api.depends('length_8m', 'length_4m', 'no_8m_bays', 'no_4m_spans')
    def _compute_total_area(self):
        for record in self:
            # Basic area calculation: length * width for both bay types
            area_8m = record.length_8m * record.no_8m_bays * record.grid_size_bay
            area_4m = record.length_4m * record.no_4m_spans * record.grid_size_span
            record.total_area = area_8m + area_4m
    
    @api.depends('total_area', 'template_id')
    def _compute_estimated_cost(self):
        for record in self:
            # Rough estimation based on template and area
            if record.template_id and record.total_area:
                # Get average component rate from template
                avg_rate = 0
                if record.template_id.component_line_ids:
                    rates = [comp.component_id.current_rate for comp in record.template_id.component_line_ids if comp.component_id.current_rate]
                    if rates:
                        avg_rate = sum(rates) / len(rates)
                
                # Very rough estimation
                record.estimated_cost = record.total_area * avg_rate * 0.1  # Rough multiplier
            else:
                record.estimated_cost = 0
    
    def action_next_step(self):
        """Move to next step in wizard"""
        if self.step == 'template':
            if not self.template_id:
                raise ValidationError(_("Please select a template to continue."))
            self.step = 'project'
        elif self.step == 'project':
            if not self.client_id:
                raise ValidationError(_("Please select a client to continue."))
            self.step = 'parameters'
        elif self.step == 'parameters':
            self.step = 'summary'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_previous_step(self):
        """Move to previous step in wizard"""
        if self.step == 'project':
            self.step = 'template'
        elif self.step == 'parameters':
            self.step = 'project'
        elif self.step == 'summary':
            self.step = 'parameters'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_create_cost_sheet(self):
        """Create the cost sheet with wizard data"""
        self.ensure_one()
        
        # Validate required fields
        if not self.template_id or not self.client_id:
            raise ValidationError(_("Template and Client are required."))
        
        # Create cost sheet
        cost_sheet_vals = {
            'template_id': self.template_id.id,
            'client_id': self.client_id.id,
            'quotation_number': self.quotation_number,
            'project_name': self.project_name,
            'site_location': self.site_location,
            'installation_position': self.installation_position,
        }
        
        cost_sheet = self.env['drkds.cost.sheet'].create(cost_sheet_vals)
        
        # Set parameter values from wizard
        self._set_parameter_values(cost_sheet)
        
        # Log creation via wizard
        self.env['drkds.change.log'].log_change(
            action_type='create',
            object_model='drkds.cost.sheet',
            object_id=cost_sheet.id,
            object_name=cost_sheet.name,
            description=f'Cost sheet "{cost_sheet.name}" created via wizard for client "{self.client_id.name}"'
        )
        
        # Return action to open the created cost sheet
        return {
            'name': _('Cost Sheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.cost.sheet',
            'res_id': cost_sheet.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _set_parameter_values(self, cost_sheet):
        """Set parameter values in the cost sheet from wizard"""
        # Define mapping between wizard fields and parameter codes
        param_mapping = {
            'length_8m': self.length_8m,
            'length_4m': self.length_4m,
            'no_8m_bays': self.no_8m_bays,
            'no_4m_spans': self.no_4m_spans,
            'grid_size_bay': self.grid_size_bay,
            'grid_size_span': self.grid_size_span,
            'corridor_length': self.corridor_length,
            'total_area': self.total_area,
        }
        
        # Update parameter values
        for param_line in cost_sheet.parameter_line_ids:
            param_code = param_line.parameter_code
            if param_code in param_mapping:
                value = param_mapping[param_code]
                if param_line.parameter_type == 'float':
                    param_line.value_float = value
                elif param_line.parameter_type == 'integer':
                    param_line.value_integer = int(value)
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Reset wizard when template changes"""
        if self.template_id:
            # Set some default values based on template type
            if self.template_id.template_type == 'nvph_8x4':
                self.length_8m = 48.0
                self.no_8m_bays = 6
                self.grid_size_bay = 8.0
            elif self.template_id.template_type == 'nvph_9x4':
                self.length_8m = 57.6  # 9.6 * 6
                self.no_8m_bays = 6
                self.grid_size_bay = 9.6
    
    def action_quick_create(self):
        """Quick create without going through all steps"""
        if not self.template_id or not self.client_id:
            raise ValidationError(_("Template and Client are required for quick create."))
        
        return self.action_create_cost_sheet()

class CostSheetTemplateWizard(models.TransientModel):
    _name = 'drkds.template.wizard'
    _description = 'Template Creation Wizard'
    
    # Basic Information
    name = fields.Char(string='Template Name', required=True)
    code = fields.Char(string='Template Code', required=True)
    description = fields.Text(string='Description')
    template_type = fields.Selection([
        ('nvph_8x4', 'NVPH 8x4'),
        ('nvph_9x4', 'NVPH 9.6x4'),
        ('rack_pinion', 'Rack and Pinion'),
        ('custom', 'Custom')
    ], string='Template Type', required=True, default='custom')
    
    # Source template for copying
    source_template_id = fields.Many2one('drkds.cost.template', string='Copy From Template')
    
    def action_create_template(self):
        """Create template"""
        self.ensure_one()
        
        # Check if code is unique
        existing = self.env['drkds.cost.template'].search([('code', '=', self.code)])
        if existing:
            raise ValidationError(_("Template code must be unique."))
        
        # Create template
        template_vals = {
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'template_type': self.template_type,
        }
        
        template = self.env['drkds.cost.template'].create(template_vals)
        
        # Copy from source template if specified
        if self.source_template_id:
            self._copy_template_structure(template)
        else:
            self._create_default_structure(template)
        
        return {
            'name': _('Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.cost.template',
            'res_id': template.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _copy_template_structure(self, new_template):
        """Copy structure from source template"""
        source = self.source_template_id
        
        # Copy parameters
        for param in source.parameter_line_ids:
            param.copy({'template_id': new_template.id})
        
        # Copy components
        for comp in source.component_line_ids:
            comp.copy({'template_id': new_template.id})
    
    def _create_default_structure(self, template):
        """Create default parameter structure"""
        # Create common parameters
        common_params = [
            {'name': 'Length at 8m Bay', 'code': 'length_8m', 'parameter_type': 'float', 'default_value': '48', 'sequence': 10},
            {'name': 'Length at 4m Span', 'code': 'length_4m', 'parameter_type': 'float', 'default_value': '48', 'sequence': 20},
            {'name': 'Number of 8m Bays', 'code': 'no_8m_bays', 'parameter_type': 'integer', 'default_value': '6', 'sequence': 30},
            {'name': 'Number of 4m Spans', 'code': 'no_4m_spans', 'parameter_type': 'integer', 'default_value': '12', 'sequence': 40},
            {'name': 'Total Area', 'code': 'total_area', 'parameter_type': 'float', 'default_value': '2304', 'sequence': 50},
            {'name': 'Grid Size (Bay)', 'code': 'grid_size_bay', 'parameter_type': 'float', 'default_value': '8', 'sequence': 60},
            {'name': 'Grid Size (Span)', 'code': 'grid_size_span', 'parameter_type': 'float', 'default_value': '4', 'sequence': 70},
        ]
        
        for param_data in common_params:
            param_data['template_id'] = template.id
            self.env['drkds.template.parameter'].create(param_data)