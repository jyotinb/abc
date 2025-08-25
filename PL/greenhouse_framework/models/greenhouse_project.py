# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from lxml import etree
import json
import logging

_logger = logging.getLogger(__name__)


class GreenhouseProject(models.Model):
    """Main project model with dynamic section tabs"""
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
    total_length = fields.Float('Total Length (m)', compute='_compute_totals', store=True)
    
    # Cache control
    needs_recalculation = fields.Boolean('Needs Recalculation', default=True)
    
    # Calculation errors
    calculation_errors = fields.Text('Calculation Errors', readonly=True)
    
    # Computed fields for summary
    structure_area = fields.Float('Structure Area', compute='_compute_structure_metrics', store=True)
    no_of_spans_calc = fields.Integer('Number of Spans', compute='_compute_structure_metrics', store=True)
    no_of_bays_calc = fields.Integer('Number of Bays', compute='_compute_structure_metrics', store=True)
    
    # Virtual fields for dynamic tabs (not stored)
    section_input_page_ids = fields.Char('Input Pages', compute='_compute_section_pages')
    section_result_page_ids = fields.Char('Result Pages', compute='_compute_section_pages')
    
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
            
            # Mark for recalculation
            self.needs_recalculation = True
    
    def _load_default_inputs(self):
        """Load default input values from greenhouse type"""
        if not self.greenhouse_type_id:
            return
            
        # Get default values from type
        defaults = self.greenhouse_type_id.get_default_inputs()
        
        # Create input lines for each section
        input_lines = []
        for section in self.active_section_ids.sorted('sequence'):
            input_fields = section.get_input_fields()
            if not input_fields:
                _logger.warning(f"No input fields defined for section {section.name}")
                continue
                
            for field_def in input_fields:
                # Validate field definition
                field_code = field_def.get('code')
                if not field_code:
                    _logger.error(f"Field definition missing 'code' in section {section.name}")
                    continue
                
                field_label = field_def.get('label', field_code.replace('_', ' ').title())
                field_type = field_def.get('type', 'float')
                
                # Get default value from type or field definition
                default_value = defaults.get(field_code, field_def.get('default', 0))
                
                # Handle selection fields properly
                if field_type == 'selection':
                    options = field_def.get('options', [])
                    if options and str(default_value) not in options:
                        default_value = options[0] if options else '0'
                
                # Handle boolean fields
                if field_type == 'boolean':
                    default_value = 'true' if default_value else 'false'
                
                # Convert value to string
                value_str = str(default_value) if default_value is not None else '0'
                
                # Prepare selection options as JSON string
                selection_options = None
                if field_type == 'selection':
                    options = field_def.get('options', [])
                    if options:
                        selection_options = json.dumps(options)
                
                input_lines.append((0, 0, {
                    'section_id': section.id,
                    'field_code': field_code,
                    'field_label': field_label,
                    'field_type': field_type,
                    'value': value_str,
                    'sequence': field_def.get('sequence', 10),
                    'help_text': field_def.get('help', ''),
                    'min_value': field_def.get('min', 0),
                    'max_value': field_def.get('max', 0),
                    'selection_options': selection_options,
                    'is_required': field_def.get('required', False),
                }))
        
        self.input_value_ids = input_lines
    
    @api.depends('component_result_ids.total_cost', 'component_result_ids.total_length')
    def _compute_totals(self):
        """Compute total cost, length and component count"""
        for project in self:
            project.total_cost = sum(project.component_result_ids.mapped('total_cost'))
            project.total_length = sum(project.component_result_ids.mapped('total_length'))
            project.total_components = len(project.component_result_ids.filtered(lambda r: r.quantity > 0))
    
    @api.depends('input_value_ids', 'input_value_ids.value')
    def _compute_structure_metrics(self):
        """Compute key structure metrics"""
        for project in self:
            # Get key dimensions
            total_span = project.get_input_value('total_span_length', 0)
            total_bay = project.get_input_value('total_bay_length', 0)
            span_width = project.get_input_value('span_width', 1)
            bay_width = project.get_input_value('bay_width', 1)
            
            # Calculate metrics
            project.structure_area = total_span * total_bay
            project.no_of_spans_calc = int(total_bay / span_width) if span_width > 0 else 0
            project.no_of_bays_calc = int(total_span / bay_width) if bay_width > 0 else 0
    
    @api.depends('active_section_ids')
    def _compute_section_pages(self):
        """Compute section pages for dynamic tabs"""
        for project in self:
            # This is just a trigger field for view updates
            project.section_input_page_ids = ','.join(project.active_section_ids.mapped('code'))
            project.section_result_page_ids = ','.join(project.active_section_ids.mapped('code'))
    
    @api.onchange('input_value_ids')
    def _onchange_input_values(self):
        """Mark for recalculation when inputs change"""
        self.needs_recalculation = True
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Dynamically modify form view to add section tabs"""
        result = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            
            # Find the input sheets page
            input_page = doc.xpath("//page[@name='input_main']")
            if input_page:
                self._inject_input_section_tabs(input_page[0], result)
            
            # Find the results sheets page
            results_page = doc.xpath("//page[@name='results_main']")
            if results_page:
                self._inject_result_section_tabs(results_page[0], result)
            
            result['arch'] = etree.tostring(doc, encoding='unicode')
        
        return result
    
    def _inject_input_section_tabs(self, parent_page, result):
        """Inject dynamic input tabs for each section"""
        # Create a notebook inside the input page
        notebook = etree.SubElement(parent_page, 'notebook')
        
        # Get all possible sections
        sections = self.env['greenhouse.section.template'].search([], order='sequence')
        
        for section in sections:
            # Skip sections without input fields
            if not section.input_fields:
                continue
            
            # Create a page for this section
            page = etree.SubElement(notebook, 'page')
            page.set('string', f'{section.icon} {section.name}')
            page.set('name', f'input_{section.code}')
            
            # Add invisibility condition based on active sections
            page.set('invisible', f"'{section.code}' not in active_section_ids.mapped('code')")
            
            # Add a group
            group = etree.SubElement(page, 'group')
            group.set('string', section.name)
            
            # Add the input field with domain filter
            field = etree.SubElement(group, 'field')
            field.set('name', 'input_value_ids')
            field.set('nolabel', '1')
            field.set('domain', f"[('section_id', '=', {section.id})]")
            field.set('context', f"{{'default_section_id': {section.id}}}")
            field.set('mode', 'tree')
            
            # Add tree view inside
            tree = etree.SubElement(field, 'tree')
            tree.set('editable', 'bottom')
            tree.set('create', 'false')
            tree.set('delete', 'false')
            
            # Add tree fields
            fields_to_add = [
                ('sequence', 'handle', None, '1'),
                ('field_label', None, 'Parameter', '1'),
                ('value', None, 'Value', None),
                ('field_type', None, None, '1'),
                ('min_value', None, 'Min', 'show'),
                ('max_value', None, 'Max', 'show'),
                ('help_text', None, 'Help', 'hide'),
            ]
            
            for fname, widget, string, invisible_or_optional in fields_to_add:
                tree_field = etree.SubElement(tree, 'field')
                tree_field.set('name', fname)
                if widget:
                    tree_field.set('widget', widget)
                if string:
                    tree_field.set('string', string)
                if invisible_or_optional == '1':
                    tree_field.set('invisible', '1')
                elif invisible_or_optional in ['show', 'hide']:
                    tree_field.set('optional', invisible_or_optional)
                if fname == 'field_label':
                    tree_field.set('readonly', '1')
        
        # Add "All Inputs" tab
        all_page = etree.SubElement(notebook, 'page')
        all_page.set('string', '📊 All Inputs')
        all_page.set('name', 'input_all')
        
        all_field = etree.SubElement(all_page, 'field')
        all_field.set('name', 'input_value_ids')
        all_field.set('nolabel', '1')
        all_field.set('mode', 'tree')
    
    def _inject_result_section_tabs(self, parent_page, result):
        """Inject dynamic result tabs for each section"""
        # Create a notebook inside the results page
        notebook = etree.SubElement(parent_page, 'notebook')
        
        # Get all possible sections
        sections = self.env['greenhouse.section.template'].search([], order='sequence')
        
        for section in sections:
            # Create a page for this section
            page = etree.SubElement(notebook, 'page')
            page.set('string', f'{section.icon} {section.name}')
            page.set('name', f'result_{section.code}')
            
            # Add invisibility condition
            page.set('invisible', f"'{section.code}' not in active_section_ids.mapped('code')")
            
            # Add the result field with domain filter
            field = etree.SubElement(page, 'field')
            field.set('name', 'component_result_ids')
            field.set('nolabel', '1')
            field.set('readonly', '1')
            field.set('domain', f"[('section_id', '=', {section.id})]")
            field.set('mode', 'tree')
            
            # Add tree view
            tree = etree.SubElement(field, 'tree')
            tree.set('create', 'false')
            tree.set('delete', 'false')
            
            # Add tree fields
            fields_to_add = [
                ('sequence', None, '#'),
                ('name', None, 'Component'),
                ('quantity', None, 'Quantity'),
                ('length', None, 'Length/Unit'),
                ('total_length', None, 'Total Length'),
                ('pipe_type', None, 'Pipe Type'),
                ('pipe_size', None, 'Pipe Size'),
            ]
            
            for fname, widget, string in fields_to_add:
                tree_field = etree.SubElement(tree, 'field')
                tree_field.set('name', fname)
                if string:
                    tree_field.set('string', string)
                if fname in ['quantity', 'total_length']:
                    tree_field.set('sum', 'Total')
                if fname in ['pipe_type', 'pipe_size']:
                    tree_field.set('optional', 'show')
        
        # Add "All Results" tab
        all_page = etree.SubElement(notebook, 'page')
        all_page.set('string', '📊 All Results')
        all_page.set('name', 'result_all')
        
        all_field = etree.SubElement(all_page, 'field')
        all_field.set('name', 'component_result_ids')
        all_field.set('nolabel', '1')
        all_field.set('readonly', '1')
        all_field.set('mode', 'tree')
        
        # Add summary group
        group = etree.SubElement(all_page, 'group')
        group.set('class', 'oe_subtotal_footer oe_right')
        
        for fname, string in [('total_components', 'Total Components'), 
                              ('total_length', 'Total Length (m)'),
                              ('total_cost', 'Total Cost')]:
            field = etree.SubElement(group, 'field')
            field.set('name', fname)
            field.set('string', string)
            field.set('readonly', '1')
            if fname == 'total_cost':
                field.set('widget', 'monetary')
                field.set('class', 'oe_subtotal_footer_separator')
    
    # Action Methods
    def action_calculate(self):
        """Calculate all components using calculation engine"""
        # This method will be overridden by greenhouse_calculation.py
        self.ensure_one()
        
        # Clear existing results
        self.component_result_ids.unlink()
        
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
        self.calculation_errors = False
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Reset',
                'message': 'Project reset to draft successfully!',
                'type': 'info',
            }
        }
    
    def action_confirm(self):
        """Confirm the project"""
        self.ensure_one()
        if self.state != 'calculated':
            raise ValidationError("Please calculate the project first!")
        
        if self.calculation_errors:
            raise ValidationError("Cannot confirm project with calculation errors!")
        
        self.state = 'confirmed'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Confirmed',
                'message': 'Project confirmed successfully!',
                'type': 'success',
            }
        }
    
    def action_refresh_sections(self):
        """Refresh section tabs after changing greenhouse type"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_load_all_sections(self):
        """Load all available sections for testing"""
        self.ensure_one()
        all_sections = self.env['greenhouse.section.template'].search([])
        self.active_section_ids = [(6, 0, all_sections.ids)]
        self._load_default_inputs()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sections Loaded',
                'message': f'Loaded {len(all_sections)} sections',
                'type': 'success',
            }
        }
    
    def action_export_excel(self):
        """Export results to Excel format"""
        # TODO: Implement Excel export
        raise ValidationError("Excel export will be implemented in the next phase")
    
    # Helper Methods
    def get_input_value(self, field_code, default=0):
        """Get input value by field code - like Excel cell reference"""
        self.ensure_one()
        value = self.input_value_ids.filtered(lambda x: x.field_code == field_code)
        if value:
            typed_value = value[0].get_typed_value()
            return typed_value if typed_value is not None else default
        return default
    
    def set_input_value(self, field_code, value):
        """Set input value by field code"""
        self.ensure_one()
        input_val = self.input_value_ids.filtered(lambda x: x.field_code == field_code)
        if input_val:
            input_val[0].value = str(value)
        else:
            # Create new input if doesn't exist
            self.input_value_ids = [(0, 0, {
                'field_code': field_code,
                'field_label': field_code.replace('_', ' ').title(),
                'value': str(value),
            })]
        self.needs_recalculation = True
    
    def get_all_input_values(self):
        """Get all input values as dictionary"""
        self.ensure_one()
        values = {}
        for input_val in self.input_value_ids:
            values[input_val.field_code] = input_val.get_typed_value()
        return values