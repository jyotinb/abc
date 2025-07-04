from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from math import ceil, sqrt 

class LengthMaster(models.Model):
    _name = 'length.master'
    _description = 'Lengths'
    _order = 'length_value asc'
        
    length_value = fields.Float(string='Length Value', required=True)
    available_for_fields = fields.Many2many(
        'ir.model.fields',
        string='Available For Fields',
        domain="[('model', '=', 'green.master')]"
    )
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('length_value')
    def _compute_display_name(self):
        for record in self:
            record.display_name = str(record.length_value)

class ComponentLine(models.Model):
    _name = 'component.line'
    _description = 'Component Line'
    
    green_master_id = fields.Many2one('green.master', string='Green Master', ondelete='cascade')
    section = fields.Selection([
        ('asc', 'ASC Components'),
        ('frame', 'Frame Components'),
        ('truss', 'Truss Components'),
        ('lower', 'Lower Section Components'),
    ], string='Section', required=True)
    
    name = fields.Char(string='Component Name', required=True)
    required = fields.Boolean(string='Required', default=True)
    nos = fields.Integer(string='Nos', default=0)
    length = fields.Float(string='Length', default=0.0)
    pipe_id = fields.Many2one('pipe.management', string='Pipe Type')
    
    # Computed fields for pipe details
    pipe_type = fields.Char(string='Pipe Type', related='pipe_id.name.name', readonly=True)
    pipe_size = fields.Float(string='Size (mm)', related='pipe_id.pipe_size.size_in_mm', readonly=True)
    wall_thickness = fields.Float(string='WT (mm)', related='pipe_id.wall_thickness.thickness_in_mm', readonly=True)
    weight_per_unit = fields.Float(string='Weight/Unit', related='pipe_id.weight', readonly=True)
    rate_per_kg = fields.Float(string='Rate/Kg', related='pipe_id.rate', readonly=True)
    
    # Calculations
    total_length = fields.Float(string='Total Length', compute='_compute_totals', store=True)
    total_weight = fields.Float(string='Total Weight', compute='_compute_totals', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_totals', store=True)
    
    @api.depends('nos', 'length', 'weight_per_unit', 'rate_per_kg')
    def _compute_totals(self):
        for record in self:
            record.total_length = record.nos * record.length
            record.total_weight = record.total_length * record.weight_per_unit
            record.total_cost = record.total_weight * record.rate_per_kg

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
    
    # Length master relationships for configurable lengths
    length_support_hockeys = fields.Many2one(
        'length.master', string='Length for Support Hockey'
    )
    length_v_support_bottom_chord_frame = fields.Many2one(
        'length.master', string='Length for V Support Bottom Chord'
    )
    length_arch_support_big = fields.Many2one(
        'length.master', string='Length for Arch Support Big'
    )
    length_arch_support_small_big_arch = fields.Many2one(
        'length.master', string='Length for Arch Support Small for Big Arch'
    )
    length_arch_support_small_small_arch = fields.Many2one(
        'length.master', string='Length for Arch Support Small for Small Arch'
    )
    length_vent_big_arch_support = fields.Many2one(
        'length.master', string='Length for Vent Support for Big Arch'
    )
    length_vent_small_arch_support = fields.Many2one(
        'length.master', string='Length for Vent Support for Small Arch'
    )
    length_side_screen_roll_up_pipe_joiner = fields.Many2one(
        'length.master', string='Length for Side Screen Roll Up Pipe Joiner'
    )
    length_side_screen_guard = fields.Many2one(
        'length.master', string='Length for Side Screen Guard'
    )
    length_front_back_c_c_cross_bracing_x = fields.Many2one(
        'length.master', string='Length for Front Back Column to Column Cross Bracing X'
    )
    length_middle_c_c_cross_bracing_x = fields.Many2one(
        'length.master', string='Length for Internal CC Cross Bracing X'
    )
    length_cross_bracing_column_arch = fields.Many2one(
        'length.master', string='Length for Cross Bracing Column Arch'
    )
    length_cross_bracing_column_bottom = fields.Many2one(
        'length.master', string='Length for Cross Bracing Column Bottom'
    )
    length_side_screen_guard_spacer = fields.Many2one(
        'length.master', string='Length for Side Screen Guard Spacer'
    )
    length_side_screen_guard_box_h_pipe = fields.Many2one(
        'length.master', string='Length for Side Screen Guard Box H Pipe'
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
    
    def _calculate_components(self):
        """Calculate all components - complete migration from greenh"""
        component_vals = []
        
        # Calculate basic dimensions first
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        arch_big = (self.no_of_bays + 1) * self.no_of_spans
        arch_small = arch_big
        
        # =============================================
        # ASC COMPONENTS
        # =============================================
        if self.is_side_coridoors:
            # ASC Pipe Support (Hockey Support)
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
                })
            
            # Back Span ASC
            if self.width_back_span_coridoor > 0:
                no_back_span_hockeys = ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
                total_hockeys += no_back_span_hockeys
                
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'asc',
                    'name': 'Back Span ASC Pipes',
                    'required': True,
                    'nos': int(no_back_span_hockeys),
                    'length': 1 + sqrt(self.width_back_span_coridoor ** 2 + self.column_height ** 2),
                })
            
            # Front Bay ASC
            if self.width_front_bay_coridoor > 0:
                no_front_bay_hockeys = (self.span_length / self.bay_width) + 1
                total_hockeys += no_front_bay_hockeys
                
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'asc',
                    'name': 'Left Bay ASC Pipes',
                    'required': True,
                    'nos': int(no_front_bay_hockeys),
                    'length': 1 + sqrt(self.width_front_bay_coridoor ** 2 + self.column_height ** 2),
                })
            
            # Back Bay ASC
            if self.width_back_bay_coridoor > 0:
                no_back_bay_hockeys = (self.span_length / self.bay_width) + 1
                total_hockeys += no_back_bay_hockeys
                
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'asc',
                    'name': 'Right Bay ASC Pipes',
                    'required': True,
                    'nos': int(no_back_bay_hockeys),
                    'length': 1 + sqrt(self.width_back_bay_coridoor ** 2 + self.column_height ** 2),
                })
            
            # ASC Pipe Support
            if self.support_hockeys > 0 and total_hockeys > 0:
                support_length = self.length_support_hockeys.length_value if self.length_support_hockeys else 1.5
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'asc',
                    'name': 'ASC Pipe Support',
                    'required': True,
                    'nos': self.support_hockeys * int(total_hockeys),
                    'length': support_length,
                })
        
        # =============================================
        # FRAME COMPONENTS
        # =============================================
        
        # Middle Columns
        if int(self.no_column_big_frame) == 1:
            no_middle_columns = total_anchor_frames
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Middle Columns',
                'required': True,
                'nos': no_middle_columns,
                'length': self.top_ridge_height,
            })
        
        # Quadruple Columns
        if int(self.no_column_big_frame) in [2, 3]:
            no_quadruple_columns = total_anchor_frames * 2
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Quadruple Columns',
                'required': True,
                'nos': no_quadruple_columns,
                'length': self.top_ridge_height,
            })
        
        # Thick Columns
        no_thick_columns = 0
        if self.thick_column == '1':
            no_thick_columns = 4
        elif self.thick_column == '2':
            no_thick_columns = (self.no_of_bays + 1) * 2
        elif self.thick_column == '3':
            no_thick_columns = (self.no_of_spans + 1) * 2
        elif self.thick_column == '4':
            no_thick_columns = ((self.no_of_bays + 1) * 2) + ((self.no_of_spans + 1) * 2)
        
        if no_thick_columns > 0:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Thick Columns',
                'required': True,
                'nos': no_thick_columns,
                'length': self.column_height,
            })
        
        # Main Columns
        no_main_columns = ((self.no_of_spans + 1) * (self.no_of_bays + 1)) - no_thick_columns
        if no_main_columns > 0:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'frame',
                'name': 'Main Columns',
                'required': True,
                'nos': no_main_columns,
                'length': self.column_height,
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
            },
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Small Arch',
                'required': True,
                'nos': arch_small,
                'length': self.small_arch_length,
            }
        ])
        
        # Bottom Chord Components
        if self.is_bottom_chord:
            # Bottom Chord Anchor Frame calculations
            if self.no_column_big_frame == '0':
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Anchor Frame Singular',
                    'required': True,
                    'nos': total_anchor_frames,
                    'length': self.span_width/(1+int(self.no_column_big_frame)) if self.span_width <= 6 else self.span_width/2,
                })
            elif self.no_column_big_frame == '1':
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Anchor Frame Singular',
                    'required': True,
                    'nos': total_anchor_frames * 2,
                    'length': self.span_width/2,
                })
            elif self.no_column_big_frame in ['2', '3']:
                nos_multiplier = 3 if self.no_column_big_frame == '2' else 4
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Anchor Frame Singular',
                    'required': True,
                    'nos': total_anchor_frames * nos_multiplier,
                    'length': self.span_width/(nos_multiplier-1),
                })
            
            # Bottom Chord Inner Line
            if self.span_width <= 6:
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'truss',
                    'name': 'Bottom Chord Inner Line Singular',
                    'required': True,
                    'nos': total_normal_frames,
                    'length': self.span_width,
                })
            else:
                component_vals.extend([
                    {
                        'green_master_id': self.id,
                        'section': 'truss',
                        'name': 'Bottom Chord Inner Line Male',
                        'required': True,
                        'nos': total_normal_frames,
                        'length': self.span_width/2,
                    },
                    {
                        'green_master_id': self.id,
                        'section': 'truss',
                        'name': 'Bottom Chord Inner Line Female',
                        'required': True,
                        'nos': total_normal_frames,
                        'length': self.span_width/2,
                    }
                ])
            
            # V Support Bottom Chord
            if int(self.v_support_bottom_chord_frame) > 0:
                v_support_length = self.length_v_support_bottom_chord_frame.length_value if self.length_v_support_bottom_chord_frame else 1.5
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'truss',
                    'name': 'V Support Bottom Chord',
                    'required': True,
                    'nos': int(self.v_support_bottom_chord_frame) * total_normal_frames,
                    'length': v_support_length,
                })
            
            # Arch Support Straight Middle
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Straight Middle',
                'required': True,
                'nos': arch_big - total_anchor_frames,
                'length': self.top_ridge_height - self.column_height,
            })
        
        # Arch Support Components
        if self.is_arch_support_big:
            arch_support_big_length = self.length_arch_support_big.length_value if self.length_arch_support_big else 2.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Big (Both Arches)',
                'required': True,
                'nos': arch_big * 2,
                'length': arch_support_big_length,
            })
        
        if self.is_arch_support_small_big_arch:
            arch_support_small_big_length = self.length_arch_support_small_big_arch.length_value if self.length_arch_support_small_big_arch else 1.5
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Small for Big Arch',
                'required': True,
                'nos': arch_big,
                'length': arch_support_small_big_length,
            })
        
        if self.is_arch_support_small_small_arch:
            arch_support_small_small_length = self.length_arch_support_small_small_arch.length_value if self.length_arch_support_small_small_arch else 1.5
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Arch Support Small for Small Arch',
                'required': True,
                'nos': arch_small,
                'length': arch_support_small_small_length,
            })
        
        # Vent Support Components
        if int(self.no_vent_big_arch_support_frame) > 0:
            vent_big_length = self.length_vent_big_arch_support.length_value if self.length_vent_big_arch_support else 2.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Vent Support for Big Arch',
                'required': True,
                'nos': arch_big * int(self.no_vent_big_arch_support_frame),
                'length': vent_big_length,
            })
        
        if int(self.no_vent_small_arch_support_frame) > 0:
            vent_small_length = self.length_vent_small_arch_support.length_value if self.length_vent_small_arch_support else 1.5
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Vent Support for Small Arch',
                'required': True,
                'nos': self.no_of_bays * self.no_of_spans * int(self.no_vent_small_arch_support_frame),
                'length': vent_small_length,
            })
        
        # Purlin Components
        component_vals.extend([
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Big Arch Purlin',
                'required': True,
                'nos': self.no_of_bays * self.no_of_spans,
                'length': self.bay_width,
            },
            {
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Small Arch Purlin',
                'required': True,
                'nos': self.no_of_bays * self.no_of_spans,
                'length': self.bay_width,
            }
        ])
        
        # Gable Purlin
        if not self.last_span_gutter:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Gable Purlin',
                'required': True,
                'nos': self.no_of_bays * 2,
                'length': self.bay_width,
            })
        
        # Border Purlins
        if int(self.bay_side_border_purlin) > 0:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Bay Side Border Purlin',
                'required': True,
                'nos': int(self.bay_side_border_purlin) * self.no_of_bays * 2,
                'length': self.bay_width,
            })
        
        if int(self.span_side_border_purlin) > 0:
            component_vals.append({
                'green_master_id': self.id,
                'section': 'truss',
                'name': 'Span Side Border Purlin',
                'required': True,
                'nos': int(self.span_side_border_purlin) * self.no_of_spans * (int(self.no_column_big_frame) + 1) * 2,
                'length': self.span_width / (int(self.no_column_big_frame) + 1),
            })
        
        # =============================================
        # LOWER SECTION COMPONENTS
        # =============================================
        
        # Side Screen Roll Up Pipe
        side_screen_pipes = ceil((self.bay_length / 5.95) * 2) + ceil((self.span_length / 5.95) * 2)
        component_vals.append({
            'green_master_id': self.id,
            'section': 'lower',
            'name': 'Side Screen Roll Up Pipe',
            'required': True,
            'nos': side_screen_pipes,
            'length': 6.0,
        })
        
        # Side Screen Roll Up Pipe Joiner
        side_screen_joiners = side_screen_pipes - 4
        if side_screen_joiners > 0:
            joiner_length = self.length_side_screen_roll_up_pipe_joiner.length_value if self.length_side_screen_roll_up_pipe_joiner else 0.5
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Side Screen Roll Up Pipe Joiner',
                'required': True,
                'nos': side_screen_joiners,
                'length': joiner_length,
            })
        
        # Side Screen Guard
        if self.side_screen_guard:
            no_side_screen_guard = total_hockeys if 'total_hockeys' in locals() and total_hockeys > 0 else ((self.no_of_spans + 1) * (self.no_of_bays + 1))
            guard_length = self.length_side_screen_guard.length_value if self.length_side_screen_guard else 1.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Side Screen Guard',
                'required': True,
                'nos': int(no_side_screen_guard),
                'length': guard_length,
            })
        
        # Side Screen Guard Box Components
        if self.side_screen_guard_box and self.no_side_screen_guard_box > 0:
            box_h_length = self.length_side_screen_guard_box_h_pipe.length_value if self.length_side_screen_guard_box_h_pipe else 1.0
            component_vals.extend([
                {
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Side Screen Guard Box Pipe',
                    'required': True,
                    'nos': self.no_side_screen_guard_box * 2,
                    'length': self.column_height + (1.5 if 'total_hockeys' in locals() and total_hockeys > 0 else 0),
                },
                {
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Side Screen Guard Box H Pipe',
                    'required': True,
                    'nos': self.no_side_screen_guard_box * 2,
                    'length': box_h_length,
                }
            ])
        
        # Cross Bracing Components
        if self.front_back_c_c_cross_bracing_x:
            front_back_length = self.length_front_back_c_c_cross_bracing_x.length_value if self.length_front_back_c_c_cross_bracing_x else 2.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Front & Back Column to Column Cross Bracing X',
                'required': True,
                'nos': (self.no_of_spans + 1) * 4,
                'length': front_back_length,
            })
        
        if self.middle_c_c_cross_bracing_x > 0:
            middle_length = self.length_middle_c_c_cross_bracing_x.length_value if self.length_middle_c_c_cross_bracing_x else 2.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Internal Column to Column Cross Bracing X',
                'required': True,
                'nos': self.middle_c_c_cross_bracing_x * (self.no_of_spans + 1) * 2,
                'length': middle_length,
            })
        
        if self.cross_bracing_column_arch:
            arch_bracing_length = self.length_cross_bracing_column_arch.length_value if self.length_cross_bracing_column_arch else 3.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Cross Bracing Column to Arch',
                'required': True,
                'nos': self.no_of_spans * 4,
                'length': arch_bracing_length,
            })
        
        if self.cross_bracing_column_bottom:
            bottom_bracing_length = self.length_cross_bracing_column_bottom.length_value if self.length_cross_bracing_column_bottom else 2.0
            component_vals.append({
                'green_master_id': self.id,
                'section': 'lower',
                'name': 'Cross Bracing Column to Bottom Chord',
                'required': True,
                'nos': self.no_of_spans * 4,
                'length': bottom_bracing_length,
            })
        
        # Arch Middle Purlin Components
        if self.arch_middle_purlin_big_arch != '0' and int(self.arch_middle_purlin_big_arch_pcs) > 0:
            nos_calc = 0
            if self.arch_middle_purlin_big_arch == '1':  # 4 Corners
                nos_calc = int(self.arch_middle_purlin_big_arch_pcs) * 4
            elif self.arch_middle_purlin_big_arch == '2':  # Front & Back
                nos_calc = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_spans * 2)
            elif self.arch_middle_purlin_big_arch == '3':  # Both Sides
                nos_calc = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_bays * 2)
            elif self.arch_middle_purlin_big_arch == '4':  # All 4 Side
                nos_calc = int(self.arch_middle_purlin_big_arch_pcs) * ((self.no_of_spans * 2) + (self.no_of_bays * 2))
            elif self.arch_middle_purlin_big_arch == '5':  # 4 Sides
                nos_calc = int(self.arch_middle_purlin_big_arch_pcs) * ((self.no_of_spans * 2) + (self.no_of_bays * 2) - 4)
            elif self.arch_middle_purlin_big_arch == '6':  # All
                nos_calc = int(self.arch_middle_purlin_big_arch_pcs) * (self.no_of_spans * self.no_of_bays)
            
            if nos_calc > 0:
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Arch Middle Purlin Big Arch',
                    'required': True,
                    'nos': nos_calc,
                    'length': self.bay_width,
                })
        
        if self.arch_middle_purlin_small_arch != '0' and int(self.arch_middle_purlin_small_arch_pcs) > 0:
            if self.arch_middle_purlin_small_arch == '1':  # 4 Corners
                nos_calc = int(self.arch_middle_purlin_small_arch_pcs) * 4
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Arch Middle Purlin Small Arch',
                    'required': True,
                    'nos': nos_calc,
                    'length': self.bay_width,
                })
        
        # Side Screen Guard Spacer
        if self.side_screen_guard or self.side_screen_guard_box:
            no_spacers = 0
            if self.side_screen_guard:
                no_spacers += int(no_side_screen_guard) * 2 if 'no_side_screen_guard' in locals() else 0
            if self.side_screen_guard_box:
                no_spacers += self.no_side_screen_guard_box * 4
            
            if no_spacers > 0:
                spacer_length = self.length_side_screen_guard_spacer.length_value if self.length_side_screen_guard_spacer else 0.3
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Side Screen Guard Spacer',
                    'required': True,
                    'nos': no_spacers,
                    'length': spacer_length,
                })
        
        # Gutter Components
        if self.gutter_ippf_full:
            nos_gutter = 0
            if self.last_span_gutter:
                nos_gutter = (self.no_of_spans + 1) * self.no_of_bays
            else:
                nos_gutter = (self.no_of_spans - 1) * self.no_of_bays
            
            if nos_gutter > 0:
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter IPPF Full',
                    'required': True,
                    'nos': nos_gutter,
                    'length': self.bay_width + 0.04,
                })
        
        if self.gutter_ippf_drainage_extension:
            nos_drainage = 0
            if self.last_span_gutter:
                nos_drainage = (self.no_of_spans + 1) * int(self.gutter_slope)
            else:
                nos_drainage = (self.no_of_spans - 1) * int(self.gutter_slope)
            
            if nos_drainage > 0:
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter IPPF Drainage Extension',
                    'required': True,
                    'nos': nos_drainage,
                    'length': 0.5,
                })
        
        if self.gutter_funnel_ippf:
            nos_funnel = 0
            if self.last_span_gutter:
                nos_funnel = (self.no_of_spans + 1) * int(self.gutter_slope)
            else:
                nos_funnel = (self.no_of_spans - 1) * int(self.gutter_slope)
            
            if nos_funnel > 0:
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter Funnel IPPF',
                    'required': True,
                    'nos': nos_funnel,
                    'length': 0.2,
                })
        
        if self.gutter_end_cap and self.gutter_funnel_ippf and int(self.gutter_slope) == 1:
            nos_end_cap = 0
            if self.last_span_gutter:
                nos_end_cap = self.no_of_spans + 1
            else:
                nos_end_cap = self.no_of_spans - 1
            
            if nos_end_cap > 0:
                component_vals.append({
                    'green_master_id': self.id,
                    'section': 'lower',
                    'name': 'Gutter End Cap',
                    'required': True,
                    'nos': nos_end_cap,
                    'length': 0.1,
                })
        
        # Create all component lines
        self.env['component.line'].create(component_vals)

    def print_report(self):
        return self.env.ref('greenh.report_print_green_master').report_action(self)

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

    # Onchange methods for better UX
    @api.onchange('is_bottom_chord')
    def _onchange_is_bottom_chord(self):
        if not self.is_bottom_chord:
            self.v_support_bottom_chord_frame = '0'

    @api.onchange('no_column_big_frame')
    def _onchange_no_column_big_frame(self):
        if self.no_column_big_frame == '0':
            self.no_anchor_frame_lines = 0

    @api.onchange('thick_column')
    def _onchange_thick_column(self):
        if self.thick_column == '0':
            pass  # No specific action needed

    @api.onchange('side_screen_guard_box')
    def _onchange_side_screen_guard_box(self):
        if not self.side_screen_guard_box:
            self.no_side_screen_guard_box = 0

# Pipe Models
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
            if record.name and record.pipe_size and record.wall_thickness:
                record.display_name = f'{record.name.name} / Size: {record.pipe_size.size_in_mm} mm / Thickness: {record.wall_thickness.thickness_in_mm} mm'
            else:
                record.display_name = record.name.name or 'Unnamed Pipe'
    
    _sql_constraints = [
        ('unique_pipe_combination', 
         'unique(name, pipe_size, wall_thickness)', 
         'A pipe with this type, size, and wall thickness already exists.')
    ]