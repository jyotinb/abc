from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from math import ceil, sqrt 
import logging

_logger = logging.getLogger(__name__)

class LengthMaster(models.Model):
    _name = 'length.master'
    _description = 'Length Master for Component Configuration'
    _order = 'length_value asc'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    length_value = fields.Float(string='Length Value', required=True)
    active = fields.Boolean(string='Active', default=True)
    
    # Multiple selection field approach - allows multiple field assignments
    available_for_fields = fields.Many2many(
        'length.field.option',
        'length_master_field_option_rel',
        'length_id',
        'field_option_id',
        string='Available For Fields',
        help="Select which Length Master fields this length should be available for"
    )
    
    # Length categories for organization
    length_category = fields.Selection([
        ('small', 'Small (< 1m)'),
        ('medium', 'Medium (1-3m)'),
        ('large', 'Large (> 3m)'),
    ], string='Length Category', compute='_compute_length_category', store=True)
    
    @api.depends('length_value')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.length_value}m" if record.length_value else "0.0m"
    
    @api.depends('length_value')
    def _compute_length_category(self):
        for record in self:
            if not record.length_value:
                record.length_category = 'small'
            elif record.length_value < 1.0:
                record.length_category = 'small'
            elif record.length_value <= 3.0:
                record.length_category = 'medium'
            else:
                record.length_category = 'large'
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.length_value}m" if record.length_value else "0.0m"
            result.append((record.id, name))
        return result

class LengthFieldOption(models.Model):
    _name = 'length.field.option'
    _description = 'Length Field Options'
    _order = 'display_name'
    
    name = fields.Char(string='Field Name', required=True)
    display_name = fields.Char(string='Display Name', required=True)
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

class ComponentLine(models.Model):
    _name = 'component.line'
    _description = 'Component Line with Excel-style functionality'
    _order = 'section, sequence, name'
    
    # Basic fields
    green_master_id = fields.Many2one('green.master', string='Green Master', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    section = fields.Selection([
        ('asc', 'ASC Components'),
        ('frame', 'Frame Components'), 
        ('truss', 'Truss Components'),
        ('lower', 'Lower Section Components'),
    ], string='Section', required=True)
    
    name = fields.Char(string='Component Name', required=True)
    description = fields.Text(string='Description')
    required = fields.Boolean(string='Required', default=True)
    
    # Quantity and dimensions
    nos = fields.Integer(string='Nos', default=0)
    length = fields.Float(string='Length (m)', default=0.0)
    
    # Length configuration
    use_length_master = fields.Boolean(string='Use Length Master', default=False)
    length_master_id = fields.Many2one('length.master', string='Select Length')
    custom_length = fields.Float(string='Custom Length', default=0.0)
    
    # Pipe selection
    pipe_id = fields.Many2one('pipe.management', string='Pipe Specification')
    
    # Related pipe fields (readonly) - with safety checks
    pipe_type = fields.Char(string='Pipe Type', compute='_compute_pipe_details', store=True)
    pipe_size = fields.Float(string='Size (mm)', compute='_compute_pipe_details', store=True)
    wall_thickness = fields.Float(string='WT (mm)', compute='_compute_pipe_details', store=True)
    weight_per_unit = fields.Float(string='Weight/Unit (kg/m)', compute='_compute_pipe_details', store=True)
    rate_per_kg = fields.Float(string='Rate/Kg', compute='_compute_pipe_details', store=True)
    
    # Calculated fields
    total_length = fields.Float(string='Total Length (m)', compute='_compute_totals', store=True)
    total_weight = fields.Float(string='Total Weight (kg)', compute='_compute_totals', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_totals', store=True)
    
    # Status fields
    is_calculated = fields.Boolean(string='Auto Calculated', default=False)
    notes = fields.Text(string='Notes')
    
    @api.depends('pipe_id')
    def _compute_pipe_details(self):
        """Safely compute pipe details with error handling"""
        for record in self:
            if record.pipe_id:
                try:
                    record.pipe_type = record.pipe_id.name.name if record.pipe_id.name else ''
                    record.pipe_size = record.pipe_id.pipe_size.size_in_mm if record.pipe_id.pipe_size else 0.0
                    record.wall_thickness = record.pipe_id.wall_thickness.thickness_in_mm if record.pipe_id.wall_thickness else 0.0
                    record.weight_per_unit = record.pipe_id.weight or 0.0
                    record.rate_per_kg = record.pipe_id.rate or 0.0
                except Exception:
                    record.pipe_type = ''
                    record.pipe_size = 0.0
                    record.wall_thickness = 0.0
                    record.weight_per_unit = 0.0
                    record.rate_per_kg = 0.0
            else:
                record.pipe_type = ''
                record.pipe_size = 0.0
                record.wall_thickness = 0.0
                record.weight_per_unit = 0.0
                record.rate_per_kg = 0.0
    
    @api.depends('nos', 'length', 'weight_per_unit', 'rate_per_kg')
    def _compute_totals(self):
        for record in self:
            record.total_length = record.nos * record.length
            record.total_weight = record.total_length * (record.weight_per_unit or 0)
            record.total_cost = record.total_weight * (record.rate_per_kg or 0)
    
    @api.onchange('use_length_master', 'length_master_id', 'custom_length')
    def _onchange_length_configuration(self):
        """Update length based on master selection or custom input - FIXED VERSION"""
        # Only update length if user is actively making a change
        if self._context.get('from_ui', True):  # Only when from user interface
            if self.use_length_master and self.length_master_id:
                self.length = self.length_master_id.length_value
            elif not self.use_length_master and self.custom_length > 0:
                self.length = self.custom_length
     
    def write(self, vals):
        """Prevent length reset during save operations"""
        # Store current length state before write
        length_states = {}
        for record in self:
            length_states[record.id] = {
                'length': record.length,
                'use_length_master': record.use_length_master,
                'custom_length': record.custom_length
            }
        
        # Perform the write
        result = super().write(vals)
        
        # Restore length if it was incorrectly reset
        for record in self:
            if record.id in length_states:
                state = length_states[record.id]
                if not record.use_length_master and record.custom_length > 0:
                    # For custom length, ensure it's preserved
                    if record.length != record.custom_length:
                        super(ComponentLine, record).write({'length': record.custom_length})
                elif record.use_length_master and record.length_master_id:
                    # For length master, ensure it matches master value
                    expected_length = record.length_master_id.length_value
                    if record.length != expected_length:
                        super(ComponentLine, record).write({'length': expected_length})
        
        return result
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.section:
                try:
                    section_name = dict(record._fields['section'].selection)[record.section]
                    name = f"[{section_name}] {name}"
                except (KeyError, AttributeError):
                    pass
            result.append((record.id, name))
        return result

class GreenMaster(models.Model):
    _name = 'green.master'
    _description = 'Greenhouse Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Information
    customer = fields.Char('Customer', size=50, tracking=True)
    address = fields.Char('Address', size=200)
    city = fields.Char('City', size=50)
    mobile = fields.Char('Mobile', size=13)
    email = fields.Char('Email', size=40)
    reference = fields.Char('Reference', size=300)
    
    # Structure Details
    structure_type = fields.Selection([
        ('NVPH', 'NVPH'),
        ('NVPH2', 'NVPH2'),
    ], string='Structure Type', required=True, default='NVPH', tracking=True)
    plot_size = fields.Char('Plot Size', size=20)
    total_span_length = fields.Float('Total Span Length', tracking=True)
    total_bay_length = fields.Float('Total Bay Length', tracking=True)
    span_length = fields.Float('Span Length', compute='_compute_calculated_dimensions', store=True)
    bay_length = fields.Float('Bay Length', compute='_compute_calculated_dimensions', store=True)
    structure_size = fields.Float('Structure Size', compute='_compute_calculated_dimensions', store=True)
    gutter_length = fields.Float('Gutter Length', compute='_compute_calculated_dimensions', store=True)
    span_width = fields.Float('Span Width', default=0.00)
    bay_width = fields.Float('Bay Width', default=0.00)
    no_of_bays = fields.Integer('Number of Bays', compute='_compute_calculated_dimensions', store=True)
    no_of_spans = fields.Integer('Number of Spans', compute='_compute_calculated_dimensions', store=True)
    gutter_slope = fields.Selection([
        ('1', '1'),('2', '2')],string = 'Gutter Slope', default='1')
    last_span_gutter = fields.Boolean('Last Span Gutter', default=False)
    top_ridge_height = fields.Float('Top Ridge Height', default=0.00)
    column_height = fields.Float('Column Height', default=0.00)
    bottom_height = fields.Float('Bottom Height', compute='_compute_calculated_dimensions', store=True)
    arch_height = fields.Float('Arch Height', compute='_compute_calculated_dimensions', store=True)
    big_arch_length = fields.Float('Big Arch Length', default=0.00)
    small_arch_length = fields.Float('Small Arch Length', default=0.00)
    foundation_length = fields.Float('Foundation Length', default=0.00)
    last_span_gutter_length = fields.Integer('Last Span Gutter Length', default=0)
    
    # ASC Settings
    is_side_coridoors = fields.Boolean('Is ASC', default=False)
    width_front_span_coridoor = fields.Float('Width Front Span ASC', default=0.00)
    width_back_span_coridoor = fields.Float('Width Back Span ASC', default=0.00)
    width_front_bay_coridoor = fields.Float('Width Left Bay ASC', default=0.00)
    width_back_bay_coridoor = fields.Float('Width Right Bay ASC', default=0.00)
    support_hockeys = fields.Integer('Support per Hockey', default=0)
    
    # Frame Settings
    no_column_big_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='No of Big Column per Anchor Frame', required=True, default='0')
    no_anchor_frame_lines = fields.Integer('Number of Anchor Frame Lines', default=0)
    thick_column = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Both Bay Side'),( '3','Both Span Side'),( '4','All 4 Side')
    ], string='Thick Column Option', required=True, default='0')
    
    # Truss Settings
    is_bottom_chord = fields.Boolean('Is Bottom Chord Required ?', default=False)
    v_support_bottom_chord_frame = fields.Selection([
        ('0', '0'),('2', '2')],'V Support Bottom Chord per Frame', default='0')
    is_arch_support_big = fields.Boolean('Is Arch Support Big (Big Arch) Required ?', default=False)
    is_arch_support_big_small = fields.Boolean('Is Arch Support Big (Small Arch) Required ?', default=False)
    
    is_arch_support_small_big_arch = fields.Boolean('Is Arch Support Small for Bigger Arch Required?', default=False)
    is_arch_support_small_small_arch = fields.Boolean('Is Arch Support Small for Smaller Arch Required?', default=False)
    no_vent_big_arch_support_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')], string='Vent Support for Big Arch per Frame', required=True, default='0')
    no_vent_small_arch_support_frame = fields.Selection([
        ('0', '0'),('2', '2')], string='Vent Support for Small Arch per Frame', required=True, default='0')
    bay_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Bay Side Border Purlin', required=True, default='0')
    span_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Span Side Border Purlin', required=True, default='0')
    
    # Lower Section Settings
    side_screen_guard = fields.Boolean('Side Screen Guard', default=False)
    side_screen_guard_box = fields.Boolean('Side Screen Guard Box', default=False)
    no_side_screen_guard_box = fields.Integer('Number of Side Screen Guard Box', default=0)
    front_back_c_c_cross_bracing_x = fields.Boolean('Front & Back Column to Column Cross bracing X', default=False)
    middle_c_c_cross_bracing_x = fields.Integer('No of Internal Column lines for Column to Column Cross Bracing X', default=0)
    cross_bracing_column_arch = fields.Boolean('Cross Bracing Column to Arch', default=False)
    cross_bracing_column_bottom = fields.Boolean('Cross Bracing Column to Bottom Chord', default=False)
    arch_middle_purlin_big_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','4 Sides'),( '5','All')], string='Arch Middle Purlin Big Arch', required=True, default='0')
    arch_middle_purlin_big_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Big Arch Pcs', required=True, default='0')
    arch_middle_purlin_small_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','4 Side'),( '5','All')], string='Arch Middle Purlin Small Arch', required=True, default='0')
    arch_middle_purlin_small_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Small Arch Pcs', required=True, default='0')
    
    # NEW GUTTER DROPDOWN SYSTEM
    gutter_type = fields.Selection([
        ('none', 'None'),
        ('ippf', 'IPPF'),
        ('continuous', 'Continuous'),
    ], string='Gutter', default='none', required=True)
    
    # IPPF Gutter Fields (only show when gutter_type = 'ippf')
    gutter_ippf_full = fields.Boolean('Gutter IPPF Full', default=False)
    gutter_ippf_drainage_extension = fields.Boolean('Gutter IPPF Drainage Extension', default=False)
    gutter_funnel_ippf = fields.Boolean('Gutter Funnel IPPF', default=False)
    gutter_end_cap = fields.Boolean('Gutter End Cap', default=False)
    
    # Continuous Gutter Fields (only show when gutter_type = 'continuous')
    gutter_extension = fields.Selection([
        ('0', '0'),
        ('2', '2'),
        ('4', '4'),
    ], string='Gutter Extension', default='0')
    
    # Length master relationships with PROPER domain filtering
    length_support_hockeys = fields.Many2one(
        'length.master', 
        string='Length for Support Hockey',
        domain="[('available_for_fields.name', '=', 'length_support_hockeys'), ('active', '=', True)]"
    )
    length_v_support_bottom_chord_frame = fields.Many2one(
        'length.master', 
        string='Length for V Support Bottom Chord',
        domain="[('available_for_fields.name', '=', 'length_v_support_bottom_chord_frame'), ('active', '=', True)]"
    )
    length_arch_support_big = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Big for Big Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_big'), ('active', '=', True)]"
    )
    length_arch_support_big_small = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Big for Small Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_big_small'), ('active', '=', True)]"
    )
    length_arch_support_small_big_arch = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Small for Big Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_small_big_arch'), ('active', '=', True)]"
    )
    length_arch_support_small_small_arch = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Small for Small Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_small_small_arch'), ('active', '=', True)]"
    )
    length_vent_big_arch_support = fields.Many2one(
        'length.master', 
        string='Length for Vent Support for Big Arch',
        domain="[('available_for_fields.name', '=', 'length_vent_big_arch_support'), ('active', '=', True)]"
    )
    length_vent_small_arch_support = fields.Many2one(
        'length.master', 
        string='Length for Vent Support for Small Arch',
        domain="[('available_for_fields.name', '=', 'length_vent_small_arch_support'), ('active', '=', True)]"
    )
    length_side_screen_roll_up_pipe_joiner = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Roll Up Pipe Joiner',
        domain="[('available_for_fields.name', '=', 'length_side_screen_roll_up_pipe_joiner'), ('active', '=', True)]"
    )
    length_side_screen_guard = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard'), ('active', '=', True)]"
    )
    length_side_screen_guard_spacer = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard Spacer',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_spacer'), ('active', '=', True)]"
    )
    length_front_back_c_c_cross_bracing_x = fields.Many2one(
        'length.master', 
        string='Length for Front Back Column to Column Cross Bracing X',
        domain="[('available_for_fields.name', '=', 'length_front_back_c_c_cross_bracing_x'), ('active', '=', True)]"
    )
    length_middle_c_c_cross_bracing_x = fields.Many2one(
        'length.master', 
        string='Length for Internal CC Cross Bracing X',
        domain="[('available_for_fields.name', '=', 'length_middle_c_c_cross_bracing_x'), ('active', '=', True)]"
    )
    length_cross_bracing_column_arch = fields.Many2one(
        'length.master', 
        string='Length for Cross Bracing Column Arch',
        domain="[('available_for_fields.name', '=', 'length_cross_bracing_column_arch'), ('active', '=', True)]"
    )
    length_cross_bracing_column_bottom = fields.Many2one(
        'length.master', 
        string='Length for Cross Bracing Column Bottom',
        domain="[('available_for_fields.name', '=', 'length_cross_bracing_column_bottom'), ('active', '=', True)]"
    )
    length_side_screen_guard_box_h_pipe = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard Box H Pipe',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_box_h_pipe'), ('active', '=', True)]"
    )
    
    # Component Lines
    asc_component_ids = fields.One2many('component.line', 'green_master_id', 
                                       domain=[('section', '=', 'asc')], 
                                       string='ASC Components')
    frame_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'frame')], 
                                         string='Frame Components')
    truss_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'truss')], 
                                         string='Truss Components')
    lower_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'lower')], 
                                         string='Lower Section Components')
    
    # Summary Totals
    total_asc_cost = fields.Float('Total ASC Cost', compute='_compute_section_totals', store=True)
    total_frame_cost = fields.Float('Total Frame Cost', compute='_compute_section_totals', store=True)
    total_truss_cost = fields.Float('Total Truss Cost', compute='_compute_section_totals', store=True)
    total_lower_cost = fields.Float('Total Lower Cost', compute='_compute_section_totals', store=True)
    grand_total_cost = fields.Float('Grand Total Cost', compute='_compute_section_totals', store=True)

    @api.depends('total_span_length', 'total_bay_length', 'width_front_span_coridoor', 'width_back_span_coridoor',
                 'width_front_bay_coridoor', 'width_back_bay_coridoor', 'span_width', 'bay_width', 
                 'column_height', 'top_ridge_height')
    def _compute_calculated_dimensions(self):
        for record in self:
            # Calculate span_length and bay_length
            record.span_length = record.total_span_length - (record.width_front_span_coridoor + record.width_back_span_coridoor)
            record.bay_length = record.total_bay_length - (record.width_front_bay_coridoor + record.width_back_bay_coridoor)

            # Calculate structure_size
            record.structure_size = (
                (record.span_length + record.width_front_span_coridoor + record.width_back_span_coridoor) *
                (record.bay_length + record.width_front_bay_coridoor + record.width_back_bay_coridoor)
            )

            # Calculate number of bays and spans
            record.no_of_bays = int(record.span_length / record.bay_width) if record.bay_width else 0
            record.no_of_spans = int(record.bay_length / record.span_width) if record.span_width else 0

            # Calculate bottom_height and arch_height
            record.bottom_height = record.column_height
            record.arch_height = record.top_ridge_height - record.column_height
            record.gutter_length = record.span_length
    
    @api.depends('asc_component_ids.total_cost', 'frame_component_ids.total_cost', 
                 'truss_component_ids.total_cost', 'lower_component_ids.total_cost')
    def _compute_section_totals(self):
        for record in self:
            record.total_asc_cost = sum(record.asc_component_ids.mapped('total_cost'))
            record.total_frame_cost = sum(record.frame_component_ids.mapped('total_cost'))
            record.total_truss_cost = sum(record.truss_component_ids.mapped('total_cost'))
            record.total_lower_cost = sum(record.lower_component_ids.mapped('total_cost'))
            record.grand_total_cost = (record.total_asc_cost + record.total_frame_cost + 
                                     record.total_truss_cost + record.total_lower_cost)

    # NEW GUTTER ONCHANGE METHODS
    @api.onchange('gutter_type')
    def _onchange_gutter_type(self):
        """Reset gutter fields when gutter type changes"""
        if self.gutter_type == 'none':
            # Reset all gutter fields
            self.gutter_ippf_full = False
            self.gutter_ippf_drainage_extension = False
            self.gutter_funnel_ippf = False
            self.gutter_end_cap = False
            self.gutter_extension = '0'
        elif self.gutter_type == 'ippf':
            # Reset continuous fields
            self.gutter_extension = '0'
        elif self.gutter_type == 'continuous':
            # Reset IPPF fields
            self.gutter_ippf_full = False
            self.gutter_ippf_drainage_extension = False
            self.gutter_funnel_ippf = False
            self.gutter_end_cap = False

    # ==============================================
    # SIMPLE DUPLICATION METHODS
    # ==============================================

    def copy(self, default=None):
        """
        Simple copy method that preserves all component data and pipe selections
        """
        if default is None:
            default = {}
        
        # Capture all component data before copying
        components_data = self._save_all_components()
        
        # Set default values for the new record
        copy_default = {
            'customer': f"{self.customer} (Copy)" if self.customer else "Project Copy",
            'asc_component_ids': [],
            'frame_component_ids': [],
            'truss_component_ids': [],
            'lower_component_ids': [],
        }
        copy_default.update(default)
        
        # Create the new record
        new_record = super(GreenMaster, self).copy(copy_default)
        
        # Recreate all components
        self._restore_all_components(new_record, components_data)
        
        return new_record

    def _save_all_components(self):
        """Save all component data for duplication"""
        components_data = []
        
        all_components = (self.asc_component_ids + self.frame_component_ids + 
                         self.truss_component_ids + self.lower_component_ids)
        
        for component in all_components:
            component_data = {
                'section': component.section,
                'sequence': component.sequence,
                'name': component.name,
                'description': component.description,
                'required': component.required,
                'notes': component.notes,
                'nos': component.nos,
                'length': component.length,
                'use_length_master': component.use_length_master,
                'length_master_id': component.length_master_id.id if component.length_master_id else False,
                'custom_length': component.custom_length,
                'pipe_id': component.pipe_id.id if component.pipe_id else False,
                'is_calculated': component.is_calculated,
            }
            components_data.append(component_data)
        
        return components_data

    def _restore_all_components(self, new_record, components_data):
        """Restore all components in the new record"""
        for comp_data in components_data:
            try:
                # Create component
                component_vals = {
                    'green_master_id': new_record.id,
                    'section': comp_data['section'],
                    'sequence': comp_data['sequence'],
                    'name': comp_data['name'],
                    'description': comp_data['description'],
                    'required': comp_data['required'],
                    'notes': comp_data['notes'],
                    'nos': comp_data['nos'],
                    'length': comp_data['length'],
                    'use_length_master': comp_data['use_length_master'],
                    'custom_length': comp_data['custom_length'],
                    'is_calculated': comp_data['is_calculated'],
                }
                
                # Add length master if exists
                if comp_data['length_master_id']:
                    component_vals['length_master_id'] = comp_data['length_master_id']
                
                # Add pipe if exists
                if comp_data['pipe_id']:
                    component_vals['pipe_id'] = comp_data['pipe_id']
                
                self.env['component.line'].create(component_vals)
                
            except Exception as e:
                _logger.error(f"Failed to restore component {comp_data['name']}: {e}")

    def action_duplicate_project(self):
        """Simple action to duplicate the current project"""
        try:
            # Create a copy
            new_record = self.copy()
            
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Project Duplicated',
                    'message': f'Successfully created copy: {new_record.customer}',
                    'type': 'success',
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Duplication Failed',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                }
            }

    # =============================================
    # EXISTING CALCULATION METHODS (KEEP AS IS)
    # =============================================

    def action_calculate_process(self):
        """
        Complete recalculation method:
        1. Saves all user pipe selections and customizations
        2. Completely resets all components with fresh calculations
        3. Restores pipe selections to matching components
        4. Provides detailed feedback to user
        """
        for record in self:
            try:
                # Step 1: Save existing selections
                _logger.info(f"Starting component recalculation for {record.customer or 'Unnamed Project'}")
                saved_selections = record._save_component_selections_improved()
                
                # Step 2: Clear all existing components
                component_counts_before = {
                    'asc': len(record.asc_component_ids),
                    'frame': len(record.frame_component_ids),
                    'truss': len(record.truss_component_ids),
                    'lower': len(record.lower_component_ids),
                }
                
                record.asc_component_ids.unlink()
                record.frame_component_ids.unlink()
                record.truss_component_ids.unlink()
                record.lower_component_ids.unlink()
                
                # Step 3: Generate fresh components with new calculations
                record._calculate_all_components()
                
                # Step 4: Restore user selections
                restoration_result = record._restore_component_selections_improved(saved_selections)
                
                # Step 5: Count new components
                component_counts_after = {
                    'asc': len(record.asc_component_ids),
                    'frame': len(record.frame_component_ids),
                    'truss': len(record.truss_component_ids),
                    'lower': len(record.lower_component_ids),
                }
                
                # Step 6: Prepare detailed feedback message
                feedback_message = record._generate_recalculation_feedback(
                    saved_selections, restoration_result, 
                    component_counts_before, component_counts_after
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Components Recalculated Successfully'),
                        'message': feedback_message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
                
            except Exception as e:
                _logger.error(f"Error during component recalculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Recalculation Error'),
                        'message': f'An error occurred during recalculation: {str(e)}',
                        'type': 'danger',
                    }
                }

    def _generate_component_key(self, section, name):
        """Generate a unique key for component matching"""
        # Clean and normalize the component name for consistent matching
        clean_name = name.strip().lower()
        
        # Handle special cases where component names might vary slightly
        name_mappings = {
            'asc pipe support': 'asc_pipe_support',
            'front span asc pipes': 'front_span_asc_pipes',
            'back span asc pipes': 'back_span_asc_pipes',
            'front bay asc pipes': 'front_bay_asc_pipes',
            'back bay asc pipes': 'back_bay_asc_pipes',
            'middle columns': 'middle_columns',
            'quadruple columns': 'quadruple_columns',
            'main columns': 'main_columns',
            'thick columns': 'thick_columns',
            'big arch': 'big_arch',
            'small arch': 'small_arch',
            'bottom chord anchor frame singular': 'bottom_chord_af_singular',
            'bottom chord anchor frame male': 'bottom_chord_af_male',
            'bottom chord anchor frame female': 'bottom_chord_af_female',
            'bottom chord inner line singular': 'bottom_chord_il_singular',
            'bottom chord inner line male': 'bottom_chord_il_male',
            'bottom chord inner line female': 'bottom_chord_il_female',
            'v support bottom chord': 'v_support_bottom_chord',
            'arch support straight middle': 'arch_support_straight_middle',
            'arch support big (big arch)': 'arch_support_big_big_arch',
            'arch support big (small arch)': 'arch_support_big_small_arch',
            'arch support small for big arch': 'arch_support_small_big_arch',
            'arch support small for small arch': 'arch_support_small_small_arch',
            'vent support for big arch': 'vent_support_big_arch',
            'vent support for small arch': 'vent_support_small_arch',
            'big arch purlin': 'big_arch_purlin',
            'small arch purlin': 'small_arch_purlin',
            'gable purlin': 'gable_purlin',
            'bay side border purlin': 'bay_side_border_purlin',
            'span side border purlin': 'span_side_border_purlin',
            'side screen roll up pipe': 'side_screen_roll_up_pipe',
            'side screen roll up pipe joiner': 'side_screen_roll_up_pipe_joiner',
            'side screen guard': 'side_screen_guard',
            'side screen guard box pipe': 'side_screen_guard_box_pipe',
            'side screen guard box h pipe': 'side_screen_guard_box_h_pipe',
            'front & back column to column cross bracing x': 'front_back_cc_cross_bracing_x',
            'internal cc cross bracing x': 'internal_cc_cross_bracing_x',
            'cross bracing column to arch': 'cross_bracing_column_arch',
            'cross bracing column to bottom chord': 'cross_bracing_column_bottom',
            'arch middle purlin big arch': 'arch_middle_purlin_big_arch',
            'arch middle purlin small arch': 'arch_middle_purlin_small_arch',
            'side screen guard spacer': 'side_screen_guard_spacer',
            'gutter ippf full': 'gutter_ippf_full',
            'gutter funnel ippf': 'gutter_funnel_ippf',
            'gutter ippf drainage extension': 'gutter_ippf_drainage_extension',
            'gutter end cap': 'gutter_end_cap',
            'gutter continuous': 'gutter_continuous',
            'gutter purlin': 'gutter_purlin',
            'gutter purlin for extension': 'gutter_purlin_extension',
        }
        
        # Use mapping if available, otherwise use cleaned name
        normalized_name = name_mappings.get(clean_name, clean_name.replace(' ', '_'))
        
        return f"{section}|{normalized_name}"

    def _save_component_selections_improved(self):
        """Save all user selections with improved component matching"""
        saved_selections = {}
        
        all_components = (self.asc_component_ids + self.frame_component_ids + 
                         self.truss_component_ids + self.lower_component_ids)
        
        for component in all_components:
            # Use improved key generation
            component_key = self._generate_component_key(component.section, component.name)
            
            saved_selections[component_key] = {
                'original_name': component.name,  # Keep original name for reference
                'pipe_id': component.pipe_id.id if component.pipe_id else False,
                'pipe_display_name': component.pipe_id.display_name if component.pipe_id else '',
                'use_length_master': component.use_length_master,
                'length_master_id': component.length_master_id.id if component.length_master_id else False,
                'length_master_value': component.length_master_id.length_value if component.length_master_id else 0.0,
                'custom_length': component.custom_length,
                'required': component.required,
                'notes': component.notes or '',
                'description': component.description or '',
                'section': component.section,
            }
        
        return saved_selections

    def _restore_component_selections_improved(self, saved_selections):
        """Restore pipe selections with improved component matching"""
        if not saved_selections:
            return {
                'restored_count': 0,
                'failed_restorations': [],
                'total_saved': 0,
                'total_new_components': 0
            }
        
        all_new_components = (self.asc_component_ids + self.frame_component_ids + 
                             self.truss_component_ids + self.lower_component_ids)
        
        restored_count = 0
        failed_restorations = []
        
        for component in all_new_components:
            component_key = self._generate_component_key(component.section, component.name)
            
            if component_key in saved_selections:
                selection_data = saved_selections[component_key]
                
                try:
                    update_vals = self._build_component_update_values(selection_data)
                    component.write(update_vals)
                    restored_count += 1
                    
                    _logger.debug(f"Restored: {component.name} <- {selection_data['pipe_display_name']}")
                    
                except Exception as e:
                    error_msg = f"Component: {component.name}, Error: {str(e)}"
                    failed_restorations.append(error_msg)
                    _logger.error(f"Failed to restore {error_msg}")
        
        # Return summary information
        return {
            'restored_count': restored_count,
            'failed_restorations': failed_restorations,
            'total_saved': len(saved_selections),
            'total_new_components': len(all_new_components)
        }

    def _build_component_update_values(self, selection_data):
        """Build update values for component restoration"""
        update_vals = {
            'required': selection_data['required'],
            'notes': selection_data['notes'],
            'use_length_master': selection_data['use_length_master'],
            'custom_length': selection_data['custom_length'],
        }
        
        # Restore description if it was customized
        if selection_data['description'] and not selection_data['description'].startswith('Auto-calculated'):
            update_vals['description'] = selection_data['description']
        
        # Verify and restore pipe selection
        if selection_data['pipe_id']:
            pipe_exists = self.env['pipe.management'].browse(selection_data['pipe_id']).exists()
            if pipe_exists:
                update_vals['pipe_id'] = selection_data['pipe_id']
            else:
                _logger.warning(f"Pipe {selection_data['pipe_display_name']} no longer exists")
        
        # Verify and restore length master
        if selection_data['length_master_id']:
            length_master_exists = self.env['length.master'].browse(selection_data['length_master_id']).exists()
            if length_master_exists:
                update_vals['length_master_id'] = selection_data['length_master_id']
        
        return update_vals

    def _generate_recalculation_feedback(self, saved_selections, restoration_result, counts_before, counts_after):
        """Generate detailed feedback message for user"""
        
        # Calculate totals
        total_before = sum(counts_before.values())
        total_after = sum(counts_after.values())
        
        # Build message parts
        message_parts = [
            f"📊 RECALCULATION SUMMARY:",
            f"",
            f"Components Before: {total_before} | Components After: {total_after}",
            f"",
            f"📋 SECTION BREAKDOWN:",
        ]
        
        # Add section details
        for section in ['asc', 'frame', 'truss', 'lower']:
            section_name = section.upper()
            before_count = counts_before[section]
            after_count = counts_after[section]
            
            if before_count > 0 or after_count > 0:
                change_indicator = "📈" if after_count > before_count else "📉" if after_count < before_count else "📊"
                message_parts.append(f"  {change_indicator} {section_name}: {before_count} → {after_count}")
        
        message_parts.extend([
            f"",
            f"🔧 PIPE SELECTIONS:",
            f"  • Saved: {len(saved_selections)} selections",
            f"  • Restored: {restoration_result['restored_count']} selections",
        ])
        
        # Add warnings for failed restorations
        if restoration_result['failed_restorations']:
            message_parts.extend([
                f"  ⚠️ Failed to restore: {len(restoration_result['failed_restorations'])} selections",
                f"     (Check logs for details)"
            ])
        
        # Add new components info
        new_components = restoration_result['total_new_components'] - restoration_result['restored_count']
        if new_components > 0:
            message_parts.append(f"  ✨ New components: {new_components} (need pipe selection)")
        
        message_parts.extend([
            f"",
            f"💰 Current Total Cost: {self.grand_total_cost:,.2f}",
            f"",
            f"✅ Recalculation completed successfully!"
        ])
        
        return "\n".join(message_parts)

    def action_reset_completely(self):
        """Completely reset all components without preserving anything"""
        for record in self:
            # Clear existing component lines completely
            record.asc_component_ids.unlink()
            record.frame_component_ids.unlink()
            record.truss_component_ids.unlink()
            record.lower_component_ids.unlink()
            
            # Calculate fresh component lines
            record._calculate_all_components()
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Complete Reset'),
                'message': _('All components have been completely reset. All pipe selections have been cleared.'),
                'type': 'warning',
            }
        }

    def action_view_selection_summary(self):
        """Show a summary of current pipe selections"""
        components_with_pipes = []
        components_without_pipes = []
        
        all_components = (self.asc_component_ids + self.frame_component_ids + 
                         self.truss_component_ids + self.lower_component_ids)
        
        for component in all_components:
            if component.pipe_id:
                components_with_pipes.append(f"{component.section.upper()}: {component.name}")
            else:
                components_without_pipes.append(f"{component.section.upper()}: {component.name}")
        
        message = f"""PIPE SELECTION SUMMARY:

Components WITH pipe selections ({len(components_with_pipes)}):
{chr(10).join(components_with_pipes) if components_with_pipes else 'None'}

Components WITHOUT pipe selections ({len(components_without_pipes)}):
{chr(10).join(components_without_pipes) if components_without_pipes else 'None'}"""
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Pipe Selection Summary'),
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }

    def action_view_cost_summary(self):
        """View cost summary breakdown"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Cost Summary - {self.customer or "Greenhouse Project"}',
            'res_model': 'component.line',
            'domain': [('green_master_id', '=', self.id)],
            'view_mode': 'tree',
            'target': 'new',
            'context': {
                'search_default_group_by_section': 1,
                'default_green_master_id': self.id,
                'create': False,
            }
        }
    
    def _calculate_all_components(self):
        """Calculate ALL components with all original calculations from greenh plus NEW GUTTER LOGIC"""
        component_vals = []
        
        # =============================================
        # BASIC CALCULATIONS (from original action_calculate_process)
        # =============================================
        
        # Calculate basic values
        no_asc = 0
        if self.width_front_span_coridoor > 0:
            no_asc += 1
        if self.width_back_span_coridoor > 0:
            no_asc += 1
        if self.width_front_bay_coridoor > 0:
            no_asc += 1
        if self.width_back_bay_coridoor > 0:
            no_asc += 1
            
        # ASC Hockey calculations
        no_front_span_coridoor_hockeys = 0
        if self.width_front_span_coridoor > 0:
            no_front_span_coridoor_hockeys = ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
            
        no_back_span_coridoor_hockeys = 0
        if self.width_back_span_coridoor > 0:
            no_back_span_coridoor_hockeys = ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
            
        no_front_bay_coridoor_hockeys = 0
        if self.width_front_bay_coridoor > 0:
            no_front_bay_coridoor_hockeys = (self.span_length / self.bay_width) + 1
            
        no_back_bay_coridoor_hockeys = 0
        if self.width_back_bay_coridoor > 0:
            no_back_bay_coridoor_hockeys = (self.span_length / self.bay_width) + 1
            
        no_total_hockeys = (no_front_span_coridoor_hockeys + no_back_span_coridoor_hockeys + 
                           no_front_bay_coridoor_hockeys + no_back_bay_coridoor_hockeys)
        
        # Frame calculations
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        
        # Column calculations
        no_middle_columns = 0
        no_quadraple_columns = 0
        if int(self.no_column_big_frame) == 1:
            no_middle_columns = total_anchor_frames
        elif int(self.no_column_big_frame) == 2:
            no_quadraple_columns = total_anchor_frames * 2
        elif int(self.no_column_big_frame) == 3:
            no_middle_columns = total_anchor_frames
            no_quadraple_columns = total_anchor_frames * 2
            
        # Thick columns
        no_thick_columns = 0
        if self.thick_column == '1':
            no_thick_columns = 4
        elif self.thick_column == '2':
            no_thick_columns = (self.no_of_bays + 1) * 2
        elif self.thick_column == '3':
            no_thick_columns = (self.no_of_spans + 1) * 2
        elif self.thick_column == '4':
            no_thick_columns = ((self.no_of_bays + 1) * 2) + ((self.no_of_spans + 1) * 2)
            
        no_main_columns = ((self.no_of_spans + 1) * (self.no_of_bays + 1)) - no_thick_columns
        
        # Arch calculations
        arch_big = (self.no_of_bays + 1) * self.no_of_spans
        arch_small = arch_big
        
        # Bottom chord calculations
        bottom_chord_af_normal = 0
        bottom_chord_af_male = 0
        bottom_chord_af_female = 0
        bottom_chord_il_normal = 0
        bottom_chord_il_male = 0
        bottom_chord_il_female = 0
        
        if self.is_bottom_chord:
            if self.no_column_big_frame == '0':
                if self.span_width <= 6:
                    bottom_chord_af_normal = total_anchor_frames
                else:
                    bottom_chord_af_male = total_anchor_frames
                    bottom_chord_af_female = total_anchor_frames
            elif self.no_column_big_frame == '1':
                bottom_chord_af_normal = total_anchor_frames * 2
            elif self.no_column_big_frame == '2':
                bottom_chord_af_normal = total_anchor_frames * 3
            elif self.no_column_big_frame == '3':
                bottom_chord_af_normal = total_anchor_frames * 4
                
            if self.span_width <= 6:
                bottom_chord_il_normal = total_normal_frames
            else:
                bottom_chord_il_male = total_normal_frames
                bottom_chord_il_female = total_normal_frames
        
        # V Support Bottom Chord
        no_v_support_bottom_chord = int(self.v_support_bottom_chord_frame) * total_normal_frames
        
        # Arch Support calculations
        arch_support_staraight_middle = 0
        if self.is_bottom_chord:
            arch_support_staraight_middle = arch_big - total_anchor_frames
            
        arch_support_big = arch_big  if self.is_arch_support_big else 0
        arch_support_big_small = arch_small  if self.is_arch_support_big_small else 0
        arch_support_small_big_arch = arch_big if self.is_arch_support_small_big_arch else 0
        arch_support_small_small_arch = arch_small if self.is_arch_support_small_small_arch else 0
        
        # Vent Support calculations
        vent_big_arch_support = int(arch_big) * int(self.no_vent_big_arch_support_frame)
        vent_small_arch_support = self.no_of_bays * self.no_of_spans * int(self.no_vent_small_arch_support_frame)
        
        # Purlin calculations
        big_arch_purlin = self.no_of_bays * self.no_of_spans
        small_arch_purlin = int(big_arch_purlin)
        
        # Gable purlin calculations
        gable_purlin = 0 if self.last_span_gutter else self.no_of_bays * 2
        
        # Border purlin calculations
        no_bay_side_border_purlin = 0
        if no_front_bay_coridoor_hockeys > 0:
            no_bay_side_border_purlin = int(self.bay_side_border_purlin) * (no_front_bay_coridoor_hockeys - 1)
        else:
            no_bay_side_border_purlin = int(self.bay_side_border_purlin) * self.no_of_bays
            
        if no_back_bay_coridoor_hockeys > 0:
            no_bay_side_border_purlin += int(self.bay_side_border_purlin) * (no_back_bay_coridoor_hockeys - 1)
        else:
            no_bay_side_border_purlin += int(self.bay_side_border_purlin) * self.no_of_bays
            
        no_span_side_border_purlin = 0
        if no_front_span_coridoor_hockeys > 0:
            no_span_side_border_purlin = int(self.span_side_border_purlin) * (no_front_span_coridoor_hockeys - 1)
        else:
            no_span_side_border_purlin = int(self.span_side_border_purlin) * self.no_of_spans * (int(self.no_column_big_frame) + 1)
            
        if no_back_span_coridoor_hockeys > 0:
            no_span_side_border_purlin += int(self.span_side_border_purlin) * (no_back_span_coridoor_hockeys - 1)
        else:
            no_span_side_border_purlin += int(self.span_side_border_purlin) * self.no_of_spans * (int(self.no_column_big_frame) + 1)
        
        # Side screen calculations - Modified to depend on guard settings
        side_screen_roll_up_pipe = 0
        side_screen_roll_up_pipe_joiner = 0

        # Only calculate if either Side Screen Guard OR Side Screen Guard Box is enabled
        if self.side_screen_guard or self.side_screen_guard_box:
            side_screen_roll_up_pipe = ceil((self.bay_length / 5.95) * 2) + ceil((self.span_length / 5.95) * 2)
            side_screen_roll_up_pipe_joiner = int(side_screen_roll_up_pipe) - 4
                
        no_side_screen_guard = 0
        if self.side_screen_guard:
            no_side_screen_guard = no_total_hockeys if no_total_hockeys > 0 else ((self.no_of_spans + 1) * (self.no_of_bays + 1))
        
        # Cross bracing calculations
        no_front_back_c_c_cross_bracing_x = int(self.front_back_c_c_cross_bracing_x) * (self.no_of_spans + 1) * 4
        no_middle_c_c_cross_bracing_x = self.middle_c_c_cross_bracing_x * (self.no_of_spans + 1) * 2
        no_cross_bracing_column_arch = int(self.cross_bracing_column_arch) * (self.no_of_spans * 4)
        no_cross_bracing_column_bottom = int(self.cross_bracing_column_bottom) * (self.no_of_spans * 4)
        
        # Arch middle purlin calculations
        no_arch_middle_purlin_small_arch = 0
        if self.arch_middle_purlin_small_arch == '0':
            arch_middle_purlin_small_arch = 0
        elif self.arch_middle_purlin_small_arch == '1':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * 4
        elif self.arch_middle_purlin_small_arch == '2':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * (self.no_of_spans * 2)
        elif self.arch_middle_purlin_small_arch == '3':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * (self.no_of_bays * 2)
        elif self.arch_middle_purlin_small_arch == '4':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * ((self.no_of_spans * 2) + (self.no_of_bays * 2) - 4)
        elif self.arch_middle_purlin_small_arch == '5':
            no_arch_middle_purlin_small_arch = int(self.arch_middle_purlin_small_arch_pcs) * (self.no_of_spans * self.no_of_bays)
            
              
        no_arch_middle_purlin_big_arch = 0
        if self.arch_middle_purlin_big_arch == '0':
            no_arch_middle_purlin_big_arch = 0
        elif self.arch_middle_purlin_big_arch == '1':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * 4
        elif self.arch_middle_purlin_big_arch == '2':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_spans * 2)
        elif self.arch_middle_purlin_big_arch == '3':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_bays * 2)
        elif self.arch_middle_purlin_big_arch == '4':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * ((self.no_of_spans * 2) + (self.no_of_bays * 2) - 4)
        elif self.arch_middle_purlin_big_arch == '5':
            no_arch_middle_purlin_big_arch = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_spans * self.no_of_bays)
            
        
        # =============================================
        # NEW GUTTER CALCULATIONS LOGIC
        # =============================================
        
        # Initialize gutter variables
        no_gutter_ippf_full = 0
        no_gutter_ippf_drainage_ext = 0
        no_gutter_funnel_ippf_funnel = 0
        no_gutter_end_cap = 0
        
        # New continuous gutter variables
        no_gutters_continuous = 0
        gutter_length_continuous = 0
        gutter_purlin_length_continuous = 0
        gutter_purlin_nos_continuous = 0
        gutter_purlin_extension_nos = 0
        gutter_purlin_extension_length = 0
        
        if self.gutter_type == 'ippf':
            # IPPF Gutter calculations (original logic)
            if self.gutter_ippf_full:
                if self.last_span_gutter:
                    no_gutter_ippf_full = (self.no_of_spans + 1) * self.no_of_bays
                else:
                    no_gutter_ippf_full = (self.no_of_spans - 1) * self.no_of_bays
                    
            if self.gutter_ippf_drainage_extension:
                if self.last_span_gutter:
                    no_gutter_ippf_drainage_ext = (self.no_of_spans + 1) * int(self.gutter_slope)
                else:
                    no_gutter_ippf_drainage_ext = (self.no_of_spans - 1) * int(self.gutter_slope)
                    
            if self.gutter_funnel_ippf:
                if self.last_span_gutter:
                    no_gutter_funnel_ippf_funnel = (self.no_of_spans + 1) * int(self.gutter_slope)
                else:
                    no_gutter_funnel_ippf_funnel = (self.no_of_spans - 1) * int(self.gutter_slope)
                    
            if self.gutter_end_cap and self.gutter_funnel_ippf and int(self.gutter_slope) == 1:
                if self.last_span_gutter:
                    no_gutter_end_cap = self.no_of_spans + 1
                else:
                    no_gutter_end_cap = self.no_of_spans - 1
                    
        elif self.gutter_type == 'continuous':
            # Continuous Gutter calculations (NEW LOGIC)
            no_gutters_continuous = self.no_of_spans - 1
            gutter_length_continuous = self.span_length + int(self.gutter_extension)
            gutter_purlin_length_continuous = self.bay_width
            gutter_purlin_nos_continuous = (self.no_of_spans - 1) * self.no_of_bays * 2
            gutter_purlin_extension_nos = (self.no_of_spans - 1) * 4
            gutter_purlin_extension_length = int(self.gutter_extension)
        
        # Side screen guard box calculations
        no_side_screen_guard_box_pipe = 0
        no_side_screen_guard_box_h_pipe = 0
        if self.no_side_screen_guard_box > 0:
            no_side_screen_guard_box_pipe = self.no_side_screen_guard_box * 2
            no_side_screen_guard_box_h_pipe = self.no_side_screen_guard_box * 2
            
        # Side screen guard spacer
        side_screen_guard_spacer = (no_side_screen_guard * 2) + (self.no_side_screen_guard_box * 4)
        
        # =============================================
        # CREATE COMPONENT LINES
        # =============================================
        
        # ASC COMPONENTS
        if self.is_side_coridoors:
            # ASC Pipe Support
            if self.support_hockeys > 0 and no_total_hockeys > 0:
                support_length = self._get_length_master_value(self.length_support_hockeys, 1.5)
                component_vals.append(self._create_component_val(
                    'asc', 'ASC Pipe Support', 
                    self.support_hockeys * int(no_total_hockeys), 
                    support_length, 
                    self.length_support_hockeys
                ))
            
            # Front Span ASC Pipes
            if no_front_span_coridoor_hockeys > 0:
                length_front_span = 1 + sqrt(self.width_front_span_coridoor ** 2 + self.column_height ** 2)
                component_vals.append(self._create_component_val(
                    'asc', 'Front Span ASC Pipes', 
                    int(no_front_span_coridoor_hockeys), 
                    length_front_span
                ))
            
            # Back Span ASC Pipes
            if no_back_span_coridoor_hockeys > 0:
                length_back_span = 1 + sqrt(self.width_back_span_coridoor ** 2 + self.column_height ** 2)
                component_vals.append(self._create_component_val(
                    'asc', 'Back Span ASC Pipes', 
                    int(no_back_span_coridoor_hockeys), 
                    length_back_span
                ))
            
            # Front Bay ASC Pipes
            if no_front_bay_coridoor_hockeys > 0:
                length_front_bay = 1 + sqrt(self.width_front_bay_coridoor ** 2 + self.column_height ** 2)
                component_vals.append(self._create_component_val(
                    'asc', 'Front Bay ASC Pipes', 
                    int(no_front_bay_coridoor_hockeys), 
                    length_front_bay
                ))
            
            # Back Bay ASC Pipes
            if no_back_bay_coridoor_hockeys > 0:
                length_back_bay = 1 + sqrt(self.width_back_bay_coridoor ** 2 + self.column_height ** 2)
                component_vals.append(self._create_component_val(
                    'asc', 'Back Bay ASC Pipes', 
                    int(no_back_bay_coridoor_hockeys), 
                    length_back_bay
                ))
        
        # FRAME COMPONENTS
        if no_middle_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Middle Columns', 
                no_middle_columns, 
                self.top_ridge_height
            ))
        
        if no_quadraple_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Quadruple Columns', 
                no_quadraple_columns, 
                self.top_ridge_height
            ))
        
        if no_main_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Main Columns', 
                no_main_columns, 
                self.column_height
            ))
        
        if no_thick_columns > 0:
            component_vals.append(self._create_component_val(
                'frame', 'Thick Columns', 
                no_thick_columns, 
                self.column_height
            ))
        
        # TRUSS COMPONENTS
        if arch_big > 0:
            component_vals.append(self._create_component_val(
                'truss', 'Big Arch', 
                arch_big, 
                self.big_arch_length
            ))
        
        if arch_small > 0:
            component_vals.append(self._create_component_val(
                'truss', 'Small Arch', 
                arch_small, 
                self.small_arch_length
            ))
        
        # Bottom Chord components
        if self.is_bottom_chord:
            if bottom_chord_af_normal > 0:
                length_af_normal = self.span_width / (1 + int(self.no_column_big_frame))
                component_vals.append(self._create_component_val(
                    'truss', 'Bottom Chord Anchor Frame Singular', 
                    bottom_chord_af_normal, 
                    length_af_normal
                ))
            
            if bottom_chord_af_male > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Bottom Chord Anchor Frame Male', 
                    bottom_chord_af_male, 
                    self.span_width / 2
                ))
            
            if bottom_chord_af_female > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Bottom Chord Anchor Frame Female', 
                    bottom_chord_af_female, 
                    self.span_width / 2
                ))
            
            if bottom_chord_il_normal > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Bottom Chord Inner Line Singular', 
                    bottom_chord_il_normal, 
                    self.span_width
                ))
            
            if bottom_chord_il_male > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Bottom Chord Inner Line Male', 
                    bottom_chord_il_male, 
                    self.span_width / 2
                ))
            
            if bottom_chord_il_female > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Bottom Chord Inner Line Female', 
                    bottom_chord_il_female, 
                    self.span_width / 2
                ))
            
            if no_v_support_bottom_chord > 0:
                v_support_length = self._get_length_master_value(self.length_v_support_bottom_chord_frame, 1.5)
                component_vals.append(self._create_component_val(
                    'truss', 'V Support Bottom Chord', 
                    no_v_support_bottom_chord, 
                    v_support_length,
                    self.length_v_support_bottom_chord_frame
                ))
            
            if arch_support_staraight_middle > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Arch Support Straight Middle', 
                    arch_support_staraight_middle, 
                    self.top_ridge_height - self.column_height
                ))
        
        # Arch Support components
        if arch_support_big > 0:
            arch_support_big_length = self._get_length_master_value(self.length_arch_support_big, 2.0)
            component_vals.append(self._create_component_val(
                'truss', 'Arch Support Big (Big Arch)', 
                arch_support_big, 
                arch_support_big_length,
                self.length_arch_support_big
            ))
        
        if arch_support_big_small > 0:
            arch_support_big_small_length = self._get_length_master_value(self.length_arch_support_big_small, 2.0)
            component_vals.append(self._create_component_val(
                'truss', 'Arch Support Big (Small Arch)', 
                arch_support_big_small, 
                arch_support_big_small_length,
                self.length_arch_support_big_small
            ))
        
        if arch_support_small_big_arch > 0:
            arch_support_small_big_length = self._get_length_master_value(self.length_arch_support_small_big_arch, 1.5)
            component_vals.append(self._create_component_val(
                'truss', 'Arch Support Small for Big Arch', 
                arch_support_small_big_arch, 
                arch_support_small_big_length,
                self.length_arch_support_small_big_arch
            ))
        
        if arch_support_small_small_arch > 0:
            arch_support_small_small_length = self._get_length_master_value(self.length_arch_support_small_small_arch, 1.5)
            component_vals.append(self._create_component_val(
                'truss', 'Arch Support Small for Small Arch', 
                arch_support_small_small_arch, 
                arch_support_small_small_length,
                self.length_arch_support_small_small_arch
            ))
        
        # Vent Support components
        if vent_big_arch_support > 0:
            vent_big_length = self._get_length_master_value(self.length_vent_big_arch_support, 2.0)
            component_vals.append(self._create_component_val(
                'truss', 'Vent Support for Big Arch', 
                vent_big_arch_support, 
                vent_big_length,
                self.length_vent_big_arch_support
            ))
        
        if vent_small_arch_support > 0:
            vent_small_length = self._get_length_master_value(self.length_vent_small_arch_support, 1.5)
            component_vals.append(self._create_component_val(
                'truss', 'Vent Support for Small Arch', 
                vent_small_arch_support, 
                vent_small_length,
                self.length_vent_small_arch_support
            ))
        
        # Purlin components
        if big_arch_purlin > 0:
            component_vals.append(self._create_component_val(
                'truss', 'Big Arch Purlin', 
                big_arch_purlin, 
                self.bay_width
            ))
        
        if small_arch_purlin > 0:
            component_vals.append(self._create_component_val(
                'truss', 'Small Arch Purlin', 
                small_arch_purlin, 
                self.bay_width
            ))
        
        if gable_purlin > 0:
            component_vals.append(self._create_component_val(
                'truss', 'Gable Purlin', 
                gable_purlin, 
                self.bay_width
            ))
        
        if no_bay_side_border_purlin > 0:
            component_vals.append(self._create_component_val(
                'truss', 'Bay Side Border Purlin', 
                no_bay_side_border_purlin, 
                self.bay_width
            ))
        
        if no_span_side_border_purlin > 0:
            span_side_length = self.span_width / (int(self.no_column_big_frame) + 1)
            component_vals.append(self._create_component_val(
                'truss', 'Span Side Border Purlin', 
                no_span_side_border_purlin, 
                span_side_length
            ))
        
        # LOWER SECTION COMPONENTS
        if side_screen_roll_up_pipe > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Side Screen Roll Up Pipe', 
                side_screen_roll_up_pipe, 
                6.0
            ))
        
        if side_screen_roll_up_pipe_joiner > 0:
            joiner_length = self._get_length_master_value(self.length_side_screen_roll_up_pipe_joiner, 0.5)
            component_vals.append(self._create_component_val(
                'lower', 'Side Screen Roll Up Pipe Joiner', 
                side_screen_roll_up_pipe_joiner, 
                joiner_length,
                self.length_side_screen_roll_up_pipe_joiner
            ))
        
        if no_side_screen_guard > 0:
            guard_length = self._get_length_master_value(self.length_side_screen_guard, 1.0)
            component_vals.append(self._create_component_val(
                'lower', 'Side Screen Guard', 
                no_side_screen_guard, 
                guard_length,
                self.length_side_screen_guard
            ))
        
        if no_side_screen_guard_box_pipe > 0:
            box_pipe_length = self.column_height
            if no_total_hockeys > 0:
                box_pipe_length = self.column_height + 1.5
            component_vals.append(self._create_component_val(
                'lower', 'Side Screen Guard Box Pipe', 
                no_side_screen_guard_box_pipe, 
                box_pipe_length
            ))
        
        if no_side_screen_guard_box_h_pipe > 0:
            box_h_pipe_length = self._get_length_master_value(self.length_side_screen_guard_box_h_pipe, 1.0)
            component_vals.append(self._create_component_val(
                'lower', 'Side Screen Guard Box H Pipe', 
                no_side_screen_guard_box_h_pipe, 
                box_h_pipe_length,
                self.length_side_screen_guard_box_h_pipe
            ))
        
        # Cross Bracing components
        if no_front_back_c_c_cross_bracing_x > 0:
            front_back_bracing_length = self._get_length_master_value(self.length_front_back_c_c_cross_bracing_x, 2.5)
            component_vals.append(self._create_component_val(
                'lower', 'Front & Back Column to Column Cross Bracing X', 
                no_front_back_c_c_cross_bracing_x, 
                front_back_bracing_length,
                self.length_front_back_c_c_cross_bracing_x
            ))
        
        if no_middle_c_c_cross_bracing_x > 0:
            middle_bracing_length = self._get_length_master_value(self.length_middle_c_c_cross_bracing_x, 2.5)
            component_vals.append(self._create_component_val(
                'lower', 'Internal CC Cross Bracing X', 
                no_middle_c_c_cross_bracing_x, 
                middle_bracing_length,
                self.length_middle_c_c_cross_bracing_x
            ))
        
        if no_cross_bracing_column_arch > 0:
            column_arch_bracing_length = self._get_length_master_value(self.length_cross_bracing_column_arch, 2.0)
            component_vals.append(self._create_component_val(
                'lower', 'Cross Bracing Column to Arch', 
                no_cross_bracing_column_arch, 
                column_arch_bracing_length,
                self.length_cross_bracing_column_arch
            ))
        
        if no_cross_bracing_column_bottom > 0:
            column_bottom_bracing_length = self._get_length_master_value(self.length_cross_bracing_column_bottom, 2.0)
            component_vals.append(self._create_component_val(
                'lower', 'Cross Bracing Column to Bottom Chord', 
                no_cross_bracing_column_bottom, 
                column_bottom_bracing_length,
                self.length_cross_bracing_column_bottom
            ))
        
        # Arch Middle Purlin components
        if no_arch_middle_purlin_big_arch > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Arch Middle Purlin Big Arch', 
                no_arch_middle_purlin_big_arch, 
                self.bay_width
            ))
        if no_arch_middle_purlin_small_arch > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Arch Middle Purlin Small Arch', 
                no_arch_middle_purlin_small_arch, 
                self.bay_width
            ))
        
        if side_screen_guard_spacer > 0:
            spacer_length = self._get_length_master_value(self.length_side_screen_guard_spacer, 0.3)
            component_vals.append(self._create_component_val(
                'lower', 'Side Screen Guard Spacer', 
                side_screen_guard_spacer, 
                spacer_length,
                self.length_side_screen_guard_spacer
            ))
        
        # =============================================
        # NEW GUTTER COMPONENTS BASED ON TYPE
        # =============================================
        
        # IPPF Gutter components
        if no_gutter_ippf_full > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter IPPF Full', 
                no_gutter_ippf_full, 
                self.bay_width + 0.04
            ))
        
        if no_gutter_funnel_ippf_funnel > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Funnel IPPF', 
                no_gutter_funnel_ippf_funnel, 
                0.5  # Estimated length for funnel
            ))
        
        if no_gutter_ippf_drainage_ext > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter IPPF Drainage Extension', 
                no_gutter_ippf_drainage_ext, 
                0.3  # Estimated length for extension
            ))
        
        if no_gutter_end_cap > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter End Cap', 
                no_gutter_end_cap, 
                0.1  # Estimated length for end cap
            ))
        
        # Continuous Gutter components (NEW)
        if no_gutters_continuous > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Continuous', 
                no_gutters_continuous, 
                gutter_length_continuous
            ))
        
        if gutter_purlin_nos_continuous > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Purlin', 
                gutter_purlin_nos_continuous, 
                gutter_purlin_length_continuous
            ))
        
        if gutter_purlin_extension_nos > 0 and gutter_purlin_extension_length > 0:
            component_vals.append(self._create_component_val(
                'lower', 'Gutter Purlin For Extension', 
                gutter_purlin_extension_nos, 
                gutter_purlin_extension_length
            ))
        
        # Create all component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
            except Exception as e:
                _logger.error(f"Error creating component line {val.get('name', 'Unknown')}: {e}")

    def _get_length_master_value(self, length_master_field, default_value):
        """Safely get length value from length master field"""
        if length_master_field:
            try:
                return length_master_field.length_value
            except Exception:
                pass
        return default_value
    
    def _create_component_val(self, section, name, nos, length, length_master=None):
        """Helper method to create component value dictionary"""
        val = {
            'green_master_id': self.id,
            'section': section,
            'name': name,
            'required': True,
            'nos': int(nos),
            'length': length,
            'is_calculated': True,
            'description': f"Auto-calculated component for {section} section",
        }
        
        if length_master:
            val.update({
                'length_master_id': length_master.id,
                'use_length_master': True,
            })
        
        return val

    def print_report(self):
        return self.env.ref('green2.report_print_green_master').report_action(self)

    # Validation methods
    @api.constrains('span_width', 'bay_width', 'total_span_length', 'total_bay_length')
    def _check_dimensions(self):
        for record in self:
            if record.span_width and record.total_span_length and record.span_width > record.total_span_length:
                raise ValidationError(_('Span width cannot be greater than total span length'))
            if record.bay_width and record.total_bay_length and record.bay_width > record.total_bay_length:
                raise ValidationError(_('Bay width cannot be greater than total bay length'))

    @api.constrains('column_height', 'top_ridge_height')
    def _check_heights(self):
        for record in self:
            if record.column_height and record.top_ridge_height and record.column_height >= record.top_ridge_height:
                raise ValidationError(_('Column height must be less than top ridge height'))

    # Onchange methods
    @api.onchange('is_bottom_chord')
    def _onchange_is_bottom_chord(self):
        if not self.is_bottom_chord:
            self.v_support_bottom_chord_frame = '0'

    @api.onchange('no_column_big_frame')
    def _onchange_no_column_big_frame(self):
        if self.no_column_big_frame == '0':
            self.no_anchor_frame_lines = 0

    @api.onchange('side_screen_guard_box')
    def _onchange_side_screen_guard_box(self):
        if not self.side_screen_guard_box:
            self.no_side_screen_guard_box = 0
            
    def action_export_excel(self):
        """Export project to Excel format"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        export_url = f"{base_url}/greenhouse/export/excel/{self.id}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': export_url,
            'target': 'new',
        }

    def action_export_excel_bulk(self):
        """Export multiple projects to Excel (for tree view)"""
        if len(self) == 1:
            return self.action_export_excel()
        
        # For multiple records, we could create a zip file with multiple Excel files
        # For now, let's just export the first one
        return self[0].action_export_excel()

# Pipe Models (unchanged)
class PipeType(models.Model):
    _name = 'pipe.type'
    _description = 'Pipe Type'
    name = fields.Char(string='Pipe Type', required=True)

class PipeSize(models.Model):
    _name = 'pipe.size'
    _description = 'Pipe Size'
    name = fields.Char(string='Pipe Size', required=True)
    size_in_mm = fields.Float(string='Size in mm', required=True)

class PipeWallThickness(models.Model):
    _name = 'pipe.wall_thickness'
    _description = 'Pipe Wall Thickness'
    name = fields.Char(string='Wall Thickness', required=True)
    thickness_in_mm = fields.Float(string='Thickness in mm', required=True)

class Pipe(models.Model):
    _name = 'pipe.management'
    _description = 'Pipe Management'
    
    name = fields.Many2one('pipe.type', string='Pipe Type', required=True)
    pipe_size = fields.Many2one('pipe.size', string='Pipe Size (in mm)', required=True)
    wall_thickness = fields.Many2one('pipe.wall_thickness', string='Wall Thickness (in mm)', required=True)
    weight = fields.Float(string='Weight (in kg)', required=True)
    rate = fields.Float(string='Rate (per kg)', required=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('weight', 'rate')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.weight * record.rate
    
    @api.depends('pipe_size','wall_thickness')
    def _compute_display_name(self):
        for record in self:
            try:
                if record.name and record.pipe_size and record.wall_thickness:
                    record.display_name = f'{record.name.name} / Size: {record.pipe_size.size_in_mm} mm / Thickness: {record.wall_thickness.thickness_in_mm} mm'
                else:
                    record.display_name = record.name.name if record.name else 'Unnamed Pipe'
            except Exception:
                record.display_name = 'Unnamed Pipe'
    
    _sql_constraints = [
        ('unique_pipe_combination', 
         'unique(name, pipe_size, wall_thickness)', 
         'A pipe with this type, size, and wall thickness already exists.')
    ]