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
        """Update length based on master selection or custom input"""
        if self.use_length_master and self.length_master_id:
            self.length = self.length_master_id.length_value
        elif not self.use_length_master and self.custom_length:
            self.length = self.custom_length
    
    @api.onchange('length_master_id')
    def _onchange_length_master(self):
        if self.length_master_id:
            self.length = self.length_master_id.length_value
            self.use_length_master = True
    
    @api.onchange('custom_length')
    def _onchange_custom_length(self):
        if self.custom_length > 0:
            self.length = self.custom_length
            self.use_length_master = False
    
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
    is_arch_support_big = fields.Boolean('Is Arch Support Big (Both Arches) Required ?', default=False)
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
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','All 4 Side'),( '5','4 Sides'),( '6','All')], string='Arch Middle Purlin Big Arch', required=True, default='0')
    arch_middle_purlin_big_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Big Arch Pcs', required=True, default='0')
    arch_middle_purlin_small_arch = fields.Selection([
        ('0', '0'),( '1','4 Corners'),( '2','Front & Back'),( '3','Both Sides'),( '4','All 4 Side'),( '5','4 Sides'),( '6','All')], string='Arch Middle Purlin Small Arch', required=True, default='0')
    arch_middle_purlin_small_arch_pcs = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')], string='Arch Middle Purlin Small Arch Pcs', required=True, default='0')
    gutter_ippf_full = fields.Boolean('Gutter IPPF Full', default=False)
    gutter_ippf_drainage_extension = fields.Boolean('Gutter IPPF Drainage Extension', default=False)
    gutter_funnel_ippf = fields.Boolean('Gutter Funnel IPPF', default=False)
    gutter_end_cap = fields.Boolean('Gutter End Cap', default=False)
    
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
        string='Length for Arch Support Big',
        domain="[('available_for_fields.name', '=', 'length_arch_support_big'), ('active', '=', True)]"
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
    length_side_screen_guard_spacer = fields.Many2one(
        'length.master', 
        string='Length for Side Screen Guard Spacer',
        domain="[('available_for_fields.name', '=', 'length_side_screen_guard_spacer'), ('active', '=', True)]"
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

    def action_calculate_process(self):
        for record in self:
            # Clear existing component lines
            record.asc_component_ids.unlink()
            record.frame_component_ids.unlink()
            record.truss_component_ids.unlink()
            record.lower_component_ids.unlink()
            
            # Calculate component lines for each section
            record._calculate_components()

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
    
    def _calculate_components(self):
        """Calculate all components with safer Length Master integration"""
        component_vals = []
        
        # Calculate basic dimensions first
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        arch_big = (self.no_of_bays + 1) * self.no_of_spans
        arch_small = arch_big
        
        # =============================================
        # ASC COMPONENTS (with safer Length Master integration)
        # =============================================
        if self.is_side_coridoors:
            total_hockeys = 0
            
            # Front Span ASC
            if self.width_front_span_coridoor > 0:
                no_front_span_hockeys = ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
                total_hockeys += no_front_span_hockeys
                
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'asc',
                    'name': 'Front Span ASC Pipes',
                    'required': True,
                    'nos': int(no_front_span_hockeys),
                    'length': 1 + sqrt(self.width_front_span_coridoor ** 2 + self.column_height ** 2),
                    'is_calculated': True,
                })
            
            # ASC Pipe Support - Uses Length Master safely
            if self.support_hockeys > 0 and total_hockeys > 0:
                support_length = 1.5  # Default value
                length_master_id = False
                use_length_master = False
                
                if self.length_support_hockeys:
                    try:
                        support_length = self.length_support_hockeys.length_value
                        length_master_id = self.length_support_hockeys.id
                        use_length_master = True
                    except Exception:
                        _logger.warning("Could not get length from length_support_hockeys, using default")
                
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'asc',
                    'name': 'ASC Pipe Support',
                    'required': True,
                    'nos': self.support_hockeys * int(total_hockeys),
                    'length': support_length,
                    'length_master_id': length_master_id,
                    'use_length_master': use_length_master,
                    'is_calculated': True,
                })
        
        # =============================================
        # FRAME COMPONENTS
        # =============================================
        
        # Main Columns
        no_main_columns = ((self.no_of_spans + 1) * (self.no_of_bays + 1))
        if no_main_columns > 0:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Main Columns',
                'required': True,
                'nos': no_main_columns,
                'length': self.column_height,
                'is_calculated': True,
            })
        
        # =============================================
        # TRUSS COMPONENTS
        # =============================================
        
        # Big Arch and Small Arch
        component_vals.extend([
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Big Arch',
                'required': True,
                'nos': arch_big,
                'length': self.big_arch_length,
                'is_calculated': True,
            },
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Small Arch',
                'required': True,
                'nos': arch_small,
                'length': self.small_arch_length,
                'is_calculated': True,
            }
        ])
        
        # V Support Bottom Chord - Uses Length Master safely
        if self.is_bottom_chord and int(self.v_support_bottom_chord_frame) > 0:
            v_support_length = 1.5  # Default value
            length_master_id = False
            use_length_master = False
            
            if self.length_v_support_bottom_chord_frame:
                try:
                    v_support_length = self.length_v_support_bottom_chord_frame.length_value
                    length_master_id = self.length_v_support_bottom_chord_frame.id
                    use_length_master = True
                except Exception:
                    _logger.warning("Could not get length from length_v_support_bottom_chord_frame, using default")
            
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'V Support Bottom Chord',
                'required': True,
                'nos': int(self.v_support_bottom_chord_frame) * total_normal_frames,
                'length': v_support_length,
                'length_master_id': length_master_id,
                'use_length_master': use_length_master,
                'is_calculated': True,
            })
        
        # Arch Support Big - Uses Length Master safely
        if self.is_arch_support_big:
            arch_support_big_length = 2.0  # Default value
            length_master_id = False
            use_length_master = False
            
            if self.length_arch_support_big:
                try:
                    arch_support_big_length = self.length_arch_support_big.length_value
                    length_master_id = self.length_arch_support_big.id
                    use_length_master = True
                except Exception:
                    _logger.warning("Could not get length from length_arch_support_big, using default")
            
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Big (Both Arches)',
                'required': True,
                'nos': arch_big * 2,
                'length': arch_support_big_length,
                'length_master_id': length_master_id,
                'use_length_master': use_length_master,
                'is_calculated': True,
            })
        
        # =============================================
        # LOWER SECTION COMPONENTS
        # =============================================
        
        # Side Screen Guard - Uses Length Master safely
        if self.side_screen_guard:
            no_side_screen_guard = ((self.no_of_spans + 1) * (self.no_of_bays + 1))
            guard_length = 1.0  # Default value
            length_master_id = False
            use_length_master = False
            
            if self.length_side_screen_guard:
                try:
                    guard_length = self.length_side_screen_guard.length_value
                    length_master_id = self.length_side_screen_guard.id
                    use_length_master = True
                except Exception:
                    _logger.warning("Could not get length from length_side_screen_guard, using default")
            
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Side Screen Guard',
                'required': True,
                'nos': int(no_side_screen_guard),
                'length': guard_length,
                'length_master_id': length_master_id,
                'use_length_master': use_length_master,
                'is_calculated': True,
            })
        
        # Create all component lines with error handling
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
            except Exception as e:
                _logger.error(f"Error creating component line {val.get('name', 'Unknown')}: {e}")

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

# Pipe Models (unchanged but with better error handling)
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