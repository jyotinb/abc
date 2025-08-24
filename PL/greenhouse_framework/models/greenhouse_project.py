# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class GreenhouseProject(models.Model):
    """Main project model - like an Excel workbook"""
    _name = 'greenhouse.project'
    _description = 'Greenhouse Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char('Project Name', required=True, tracking=True)
    reference = fields.Char('Reference', readonly=True, copy=False)
    
    # Customer Information
    customer_name = fields.Char('Customer Name', required=True, tracking=True)
    customer_mobile = fields.Char('Mobile', tracking=True)
    customer_email = fields.Char('Email', tracking=True)
    customer_address = fields.Text('Address')
    
    # Project Configuration
    greenhouse_type_id = fields.Many2one(
        'greenhouse.type',
        string='Greenhouse Type',
        required=True,
        tracking=True
    )
    
    active_section_ids = fields.Many2many(
        'greenhouse.section.template',
        'project_section_rel',
        'project_id',
        'section_id',
        string='Active Sections',
        help='Sections included in this project'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Dates
    project_date = fields.Date('Project Date', default=fields.Date.today, tracking=True)
    calculation_date = fields.Datetime('Last Calculated', readonly=True)
    
    # Data Storage
    input_value_ids = fields.One2many(
        'greenhouse.input.value',
        'project_id',
        string='Input Values'
    )
    
    component_result_ids = fields.One2many(
        'greenhouse.component.result',
        'project_id',
        string='Component Results'
    )
    
    # Summary Fields (Computed)
    total_cost = fields.Float('Total Cost', compute='_compute_totals', store=True)
    total_components = fields.Integer('Total Components', compute='_compute_totals', store=True)
    
    # Cache control
    needs_recalculation = fields.Boolean('Needs Recalculation', default=True)
    
    @api.model
    def create(self, vals):
        """Generate reference on create"""
        if not vals.get('reference'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('greenhouse.project') or 'New'
        return super().create(vals)
    
    @api.onchange('greenhouse_type_id')
    def _onchange_greenhouse_type(self):
        """Load default sections and inputs when type changes"""
        if self.greenhouse_type_id:
            # Set default sections
            self.active_section_ids = self.greenhouse_type_id.section_ids
            
            # Clear existing inputs
            self.input_value_ids = [(5, 0, 0)]
            
            # Load default inputs
            self._load_default_inputs()
    
    def _load_default_inputs(self):
        """Load default input values from greenhouse type"""
        if not self.greenhouse_type_id:
            return
            
        # Get default values from type
        defaults = self.greenhouse_type_id.get_default_inputs()
        
        # Create input lines for each section
        input_lines = []
        for section in self.active_section_ids:
            for field_def in section.get_input_fields():
                value = defaults.get(field_def['code'], field_def.get('default', 0))
                input_lines.append((0, 0, {
                    'section_id': section.id,
                    'field_code': field_def['code'],
                    'field_label': field_def['label'],
                    'field_type': field_def.get('type', 'float'),
                    'value': str(value),
                    'sequence': field_def.get('sequence', 10),
                }))
        
        self.input_value_ids = input_lines
    
    @api.depends('component_result_ids.total_cost')
    def _compute_totals(self):
        """Compute total cost and component count"""
        for project in self:
            project.total_cost = sum(project.component_result_ids.mapped('total_cost'))
            project.total_components = len(project.component_result_ids)
    
    @api.onchange('input_value_ids')
    def _onchange_input_values(self):
        """Mark for recalculation when inputs change"""
        self.needs_recalculation = True
    
    # Action Methods
    def action_calculate(self):
        """Calculate all components"""
        self.ensure_one()
        
        # Clear existing results
        self.component_result_ids.unlink()
        
        # TODO: Week 2 - Implement calculation engine
        # For now, create dummy results
        self._create_dummy_results()
        
        # Update status
        self.write({
            'state': 'calculated',
            'calculation_date': fields.Datetime.now(),
            'needs_recalculation': False,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Project calculated successfully!',
                'type': 'success',
            }
        }
    
    def _create_dummy_results(self):
        """Create dummy results for testing"""
        # This will be replaced with actual calculation engine
        for section in self.active_section_ids:
            self.env['greenhouse.component.result'].create({
                'project_id': self.id,
                'section_id': section.id,
                'name': f'Sample Component for {section.name}',
                'quantity': 10,
                'length': 5.0,
                'unit_cost': 100,
                'total_cost': 500,
            })
    
    def action_reset(self):
        """Reset to draft state"""
        self.ensure_one()
        self.component_result_ids.unlink()
        self.state = 'draft'
        self.needs_recalculation = True
    
    def action_confirm(self):
        """Confirm the project"""
        self.ensure_one()
        if self.state != 'calculated':
            raise ValidationError("Please calculate the project first!")
        self.state = 'confirmed'
    
    # Helper Methods
    def get_input_value(self, field_code, default=0):
        """Get input value by field code - like Excel cell reference"""
        value = self.input_value_ids.filtered(lambda x: x.field_code == field_code)
        if value:
            return value[0].get_typed_value()
        return default
    
    def set_input_value(self, field_code, value):
        """Set input value by field code"""
        input_val = self.input_value_ids.filtered(lambda x: x.field_code == field_code)
        if input_val:
            input_val[0].value = str(value)
        else:
            # Create new input if doesn't exist
            self.input_value_ids = [(0, 0, {
                'field_code': field_code,
                'value': str(value),
            })]
