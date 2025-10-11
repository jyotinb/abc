# green2_truss/models/green_master_truss.py
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class GreenMasterTruss(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # NEW ARCH SUPPORT TYPE FIELD
    # =============================================
    arch_support_type = fields.Selection([
        ('none', 'None'),
        ('w', 'W'),
        ('m', 'M'),
        ('arch_2_bottom', 'Arch to Bottom Support'),
        ('arch_2_straight', 'Arch to Straight Middle')
    ], string='Arch Support Type', default='none', tracking=True,
       help="""Select arch support configuration:
       - W: All 4 arch supports compulsory
       - M: All 4 arch supports compulsory
       - Arch to Bottom Support: Both Small arch supports only
       - Arch to Straight Middle: Both Big arch supports only""")
    
    # Bottom Chord Configuration
    is_bottom_chord = fields.Boolean('Is Bottom Chord Required ?', default=False, tracking=True)
    v_support_bottom_chord_frame = fields.Selection([
        ('0', '0'),('2', '2')
    ], 'V Support Bottom Chord per Frame', default='0', tracking=True)
    
    # DEPRECATED - Will be auto-set based on arch_support_type
    is_arch_support_big = fields.Boolean('Is Arch Support Big (Big Arch) Required ?', 
                                        compute='_compute_arch_support_flags', store=True, tracking=True)
    is_arch_support_big_small = fields.Boolean('Is Arch Support Big (Small Arch) Required ?', 
                                              compute='_compute_arch_support_flags', store=True, tracking=True)
    is_arch_support_small_big_arch = fields.Boolean('Is Arch Support Small for Bigger Arch Required?', 
                                                    compute='_compute_arch_support_flags', store=True, tracking=True)
    is_arch_support_small_small_arch = fields.Boolean('Is Arch Support Small for Smaller Arch Required?', 
                                                      compute='_compute_arch_support_flags', store=True, tracking=True)
    
    # Vent Support Configuration
    no_vent_big_arch_support_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='Vent Support for Big Arch per Frame', required=True, default='0', tracking=True)
    
    no_vent_small_arch_support_frame = fields.Selection([
        ('0', '0'),('2', '2')
    ], string='Vent Support for Small Arch per Frame', required=True, default='0', tracking=True)
    
    # Border Purlin Configuration
    bay_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')
    ], string='Bay Side Border Purlin', required=True, default='0', tracking=True,
       help="Number of purlin lines between columns on bay side")
    
    span_side_border_purlin = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2')
    ], string='Span Side Border Purlin', required=True, default='0', tracking=True,
       help="Number of purlin lines between columns on span side")
    
    # =============================================
    # ASC SIDE CONFIGURATION
    # =============================================
    front_bay_asc = fields.Boolean(
        'Front Bay ASC', 
        compute='_compute_asc_sides',
        store=True,
        readonly=True,
        tracking=True,
        help="Auto-detected from ASC Pipes component"
    )
    
    back_bay_asc = fields.Boolean(
        'Back Bay ASC', 
        compute='_compute_asc_sides',
        store=True,
        readonly=True,
        tracking=True,
        help="Auto-detected from ASC Pipes component"
    )
    
    front_span_asc = fields.Boolean(
        'Front Span ASC', 
        compute='_compute_asc_sides',
        store=True,
        readonly=True,
        tracking=True,
        help="Auto-detected from ASC Pipes component"
    )
    
    back_span_asc = fields.Boolean(
        'Back Span ASC', 
        compute='_compute_asc_sides',
        store=True,
        readonly=True,
        tracking=True,
        help="Auto-detected from ASC Pipes component"
    )
    
    
    # =============================================
    # THICK COLUMN CONFIGURATION
    # =============================================
    thick_column_position = fields.Selection([
        ('4_corner', '4 Corner'),
        ('2_bay_side', '2 Bay Side'),
        ('2_span_side', '2 Span Side'),
        ('all_4_side', 'All 4 Side'),
        ('none', '0 Thick Column')
    ], string='Thick Column Position', default='none', tracking=True,
       help="Position of thick columns in the structure")
    
    # =============================================
    # ANCHOR FRAME CONFIGURATION
    # =============================================
    no_anchor_frame_lines = fields.Integer(
        'Anchor Frame Lines', 
        default=0, 
        tracking=True,
        help="Number of anchor frame lines"
    )
    
    # Length Master Fields for Truss
    length_v_support_bottom_chord_frame = fields.Many2one(
        'length.master', 
        string='Length for V Support Bottom Chord',
        domain="[('available_for_fields.name', '=', 'length_v_support_bottom_chord_frame'), ('active', '=', True)]",
        tracking=True
    )
    
    length_arch_support_big = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Big for Big Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_big'), ('active', '=', True)]",
        tracking=True
    )
    
    length_arch_support_big_small = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Big for Small Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_big_small'), ('active', '=', True)]",
        tracking=True
    )
    
    length_arch_support_small_big_arch = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Small for Big Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_small_big_arch'), ('active', '=', True)]",
        tracking=True
    )
    
    length_arch_support_small_small_arch = fields.Many2one(
        'length.master', 
        string='Length for Arch Support Small for Small Arch',
        domain="[('available_for_fields.name', '=', 'length_arch_support_small_small_arch'), ('active', '=', True)]",
        tracking=True
    )
    
    length_vent_big_arch_support = fields.Many2one(
        'length.master', 
        string='Length for Vent Support for Big Arch',
        domain="[('available_for_fields.name', '=', 'length_vent_big_arch_support'), ('active', '=', True)]",
        tracking=True
    )
    
    length_vent_small_arch_support = fields.Many2one(
        'length.master', 
        string='Length for Vent Support for Small Arch',
        domain="[('available_for_fields.name', '=', 'length_vent_small_arch_support'), ('active', '=', True)]",
        tracking=True
    )
    
    gutter_type = fields.Selection([
        ('none', 'None'),
        ('ippf', 'IPPF'),
        ('continuous', 'Continuous'),
    ], string='Gutter', default='none', required=True, tracking=True)
    
    
    
    @api.depends('width_front_span_coridoor', 'width_back_span_coridoor',
                 'width_front_bay_coridoor', 'width_back_bay_coridoor')
    def _compute_asc_sides(self):
        """
        Simple ASC detection from width configuration fields
        If width > 0, ASC is enabled for that side
        """
        for record in self:
            # Front Bay ASC
            record.front_bay_asc = (
                hasattr(record, 'width_front_bay_coridoor') and 
                record.width_front_bay_coridoor and 
                record.width_front_bay_coridoor > 0
            )
            
            # Back Bay ASC
            record.back_bay_asc = (
                hasattr(record, 'width_back_bay_coridoor') and 
                record.width_back_bay_coridoor and 
                record.width_back_bay_coridoor > 0
            )
            
            # Front Span ASC
            record.front_span_asc = (
                hasattr(record, 'width_front_span_coridoor') and 
                record.width_front_span_coridoor and 
                record.width_front_span_coridoor > 0
            )
            
            # Back Span ASC
            record.back_span_asc = (
                hasattr(record, 'width_back_span_coridoor') and 
                record.width_back_span_coridoor and 
                record.width_back_span_coridoor > 0
            )
    # =============================================
    # COMPUTED METHODS FOR ARCH SUPPORT FLAGS
    # =============================================
    @api.depends('arch_support_type')
    def _compute_arch_support_flags(self):
        """Auto-set arch support flags based on arch_support_type"""
        for record in self:
            if record.arch_support_type == 'w' or record.arch_support_type == 'm':
                # W or M: All 4 compulsory
                record.is_arch_support_big = True
                record.is_arch_support_big_small = True
                record.is_arch_support_small_big_arch = True
                record.is_arch_support_small_small_arch = True
            elif record.arch_support_type == 'arch_2_bottom':
                # Arch to Bottom: Both Small only
                record.is_arch_support_big = False
                record.is_arch_support_big_small = False
                record.is_arch_support_small_big_arch = True
                record.is_arch_support_small_small_arch = True
            elif record.arch_support_type == 'arch_2_straight':
                # Arch to Straight Middle: Both Big only
                record.is_arch_support_big = True
                record.is_arch_support_big_small = True
                record.is_arch_support_small_big_arch = False
                record.is_arch_support_small_small_arch = False
            else:  # 'none'
                record.is_arch_support_big = False
                record.is_arch_support_big_small = False
                record.is_arch_support_small_big_arch = False
                record.is_arch_support_small_small_arch = False
    
    @api.onchange('arch_support_type')
    def _onchange_arch_support_type(self):
        """Synchronize clamp_type when arch_support_type changes"""
        if self.arch_support_type == 'w':
            self.clamp_type = 'w_type'
        elif self.arch_support_type == 'm':
            self.clamp_type = 'm_type'
        else:
            # For 'none', 'arch_2_bottom', 'arch_2_straight'
            self.clamp_type = 'none'
    
    @api.onchange('is_bottom_chord')
    def _onchange_is_bottom_chord(self):
        if not self.is_bottom_chord:
            self.v_support_bottom_chord_frame = '0'
    
    @api.onchange('no_anchor_frame_lines')
    def _onchange_no_anchor_frame_lines(self):
        """Show message when anchor frame lines = 1"""
        if self.no_anchor_frame_lines == 1 and int(self.span_side_border_purlin or '0') > 0:
            return {
                'warning': {
                    'title': 'Anchor Frame Lines Notice',
                    'message': 'We consider Anchor Frame Lines and ASC (if there) are at same line for clamp calculations.'
                }
            }
    
    def _calculate_all_components(self):
        """Extend calculation to add truss components"""
        super()._calculate_all_components()
        self._calculate_truss_components()
    
    def _calculate_truss_components(self):
        """Calculate truss-specific components"""
        component_vals = []
        
        # Get frame calculations needed for truss
        total_anchor_frames = self.no_anchor_frame_lines * self.no_of_spans
        total_normal_frames = (self.no_of_spans * (self.no_of_bays + 1)) - total_anchor_frames
        
        # Arch calculations
        arch_big = (self.no_of_bays + 1) * self.no_of_spans
        arch_small = arch_big
        
        # Bottom Chord calculations
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
        
        # V Support calculations
        no_v_support_bottom_chord = int(self.v_support_bottom_chord_frame) * total_normal_frames
        no_v_support_bottom_chord_af = int(self.v_support_bottom_chord_frame) * total_anchor_frames
        
        # Arch Support calculations - Keep existing Arch Support Straight Middle calculation
        arch_support_staraight_middle = 0
        if self.is_bottom_chord:
            arch_support_staraight_middle = arch_big - total_anchor_frames
        
        # Arch Support calculations based on computed flags
        arch_support_big = arch_big if self.is_arch_support_big else 0
        arch_support_big_small = arch_small if self.is_arch_support_big_small else 0
        arch_support_small_big_arch = arch_big if self.is_arch_support_small_big_arch else 0
        arch_support_small_small_arch = arch_small if self.is_arch_support_small_small_arch else 0
        
        # Vent Support calculations
        vent_big_arch_support = int(arch_big) * int(self.no_vent_big_arch_support_frame)
        vent_small_arch_support = self.no_of_bays * self.no_of_spans * int(self.no_vent_small_arch_support_frame)
        
        # Purlin calculations
        big_arch_purlin = self.no_of_bays * self.no_of_spans
        small_arch_purlin = int(big_arch_purlin)
        gable_purlin = 0 if self.last_span_gutter else self.no_of_bays * 2
        
        # Border Purlin calculations
        no_bay_side_border_purlin = int(self.bay_side_border_purlin) * self.no_of_bays * 2
        no_span_side_border_purlin = int(self.span_side_border_purlin) * self.no_of_spans * (int(self.no_column_big_frame) + 1) * 2
        
        # Create Arch components
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
        
        # Create Bottom Chord components
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
            
            # V Support components
            if no_v_support_bottom_chord > 0:
                v_support_length = self._get_length_master_value(self.length_v_support_bottom_chord_frame, 1.5)
                component_vals.append(self._create_component_val(
                    'truss', 'V Support Bottom Chord', 
                    no_v_support_bottom_chord, 
                    v_support_length,
                    self.length_v_support_bottom_chord_frame
                ))
            
            if no_v_support_bottom_chord_af > 0:
                v_support_length_af = self._get_length_master_value(self.length_v_support_bottom_chord_frame, 1.5)
                component_vals.append(self._create_component_val(
                    'truss', 'V Support Bottom Chord (AF)', 
                    no_v_support_bottom_chord_af, 
                    v_support_length_af,
                    self.length_v_support_bottom_chord_frame
                ))
            
            # Keep existing Arch Support Straight Middle
            if arch_support_staraight_middle > 0:
                component_vals.append(self._create_component_val(
                    'truss', 'Arch Support Straight Middle', 
                    arch_support_staraight_middle, 
                    self.top_ridge_height - self.column_height
                ))
        
        # Arch Support components based on selection
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
        
        # Create all truss component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created truss component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating truss component {val.get('name', 'Unknown')}: {e}")