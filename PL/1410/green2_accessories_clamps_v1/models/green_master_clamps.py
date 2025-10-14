# green2_accessories_clamps/models/green_master_clamps.py
# COMPLETE IMPLEMENTATION - ALL METHODS FULLY CODED WITH BORDER PURLIN CLAMPS
# FIXED VERSION - Corrected middle column size retrieval in ASC calculations

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterClamps(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # FIELD DECLARATIONS
    # =============================================
    
    bay_side_border_purlin = fields.Integer(
        'Bay Side Border Purlin', 
        default=0,
        help="Number of bay side border purlins per segment (0=disabled, 1=1 per segment, 2=2 per segment)"
    )
    
    span_side_border_purlin = fields.Integer(
        'Span Side Border Purlin', 
        default=0,
        help="Number of span side border purlins per segment (0=disabled, 1=1 per segment, 2=2 per segment)"
    )
    
    clamp_type = fields.Selection([
        ('w_type', 'W Type'),
        ('m_type', 'M Type'),
        ('none', 'None')
    ], string='Clamp Type', compute='_compute_clamp_type', store=True, readonly=True,
       help="Automatically set based on Arch Support Type")
    
    arch_support_type = fields.Selection([
        ('none', 'None'),
        ('w', 'W Type'),
        ('m', 'M Type'),
        ('arch_2_bottom', 'Arch to Bottom'),
        ('arch_2_straight', 'Arch to Straight Middle')
    ], string='Arch Support Type', default='none', tracking=True)
    
    # Purlin clamp configurations
    big_purlin_clamp_type_first = fields.Selection([
        ('full_clamp', 'Full Clamp'),
        ('l_joint', 'L Joint'),
    ], string='Big Purlin First Type', tracking=True)
    
    big_purlin_clamp_type_second = fields.Selection([
        ('half_clamp', 'Half Clamp'),
        ('t_joint', 'T Joint'),
    ], string='Big Purlin Second Type', tracking=True)
    
    small_purlin_clamp_type_first = fields.Selection([
        ('full_clamp', 'Full Clamp'),
        ('l_joint', 'L Joint'),
    ], string='Small Purlin First Type', tracking=True)
    
    small_purlin_clamp_type_second = fields.Selection([
        ('half_clamp', 'Half Clamp'),
        ('t_joint', 'T Joint'),
    ], string='Small Purlin Second Type', tracking=True)
    
    bottom_chord_clamp_type = fields.Selection([
        ('single', 'Single'),
        ('triple', 'Triple')
    ], string='Bottom Chord Clamp Type', default='single', tracking=True)
    
    # ASC-specific fields
    bay_side_clamp_required = fields.Boolean(
        'Bay Side Clamp Required',
        default=False,
        tracking=True,
        help="For Gutter Arch Brackets: specify if bay side clamps are required"
    )
    
    # ASC side indicators (computed from ASC module)
    front_span_asc = fields.Boolean(
        'Front Span ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    back_span_asc = fields.Boolean(
        'Back Span ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    front_bay_asc = fields.Boolean(
        'Front Bay ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    back_bay_asc = fields.Boolean(
        'Back Bay ASC',
        compute='_compute_asc_sides',
        store=True,
        help="Computed from ASC width configuration"
    )
    
    # Summary fields
    clamps_size_summary = fields.Text(
        string='Clamps Size Summary',
        compute='_compute_clamps_size_summary',
        store=False
    )
    
    border_purlin_clamps_summary = fields.Text(
        string='Border Purlin Clamps Summary',
        compute='_compute_border_purlin_clamps_summary',
        store=False
    )
    
    clamps_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'clamps')],
        string='Clamps Components'
    )
    
    # =============================================
    # COMPUTED METHODS
    # =============================================
    
    @api.depends('arch_support_type')
    def _compute_clamp_type(self):
        """Compute clamp type from arch_support_type"""
        for record in self:
            if hasattr(record, 'arch_support_type'):
                if record.arch_support_type == 'w':
                    record.clamp_type = 'w_type'
                elif record.arch_support_type == 'm':
                    record.clamp_type = 'm_type'
                else:
                    record.clamp_type = 'none'
            else:
                record.clamp_type = 'none'
    
    @api.depends('width_front_span_coridoor', 'width_back_span_coridoor',
                 'width_front_bay_coridoor', 'width_back_bay_coridoor')
    def _compute_asc_sides(self):
        """Compute which ASC sides are active based on width configuration"""
        for record in self:
            record.front_span_asc = (hasattr(record, 'width_front_span_coridoor') and 
                                     record.width_front_span_coridoor > 0)
            record.back_span_asc = (hasattr(record, 'width_back_span_coridoor') and 
                                    record.width_back_span_coridoor > 0)
            record.front_bay_asc = (hasattr(record, 'width_front_bay_coridoor') and 
                                    record.width_front_bay_coridoor > 0)
            record.back_bay_asc = (hasattr(record, 'width_back_bay_coridoor') and 
                                   record.width_back_bay_coridoor > 0)
    
    @api.depends('clamps_component_ids', 'clamps_component_ids.size_specification', 
                 'clamps_component_ids.nos')
    def _compute_clamps_size_summary(self):
        """Compute summary of clamp sizes"""
        for record in self:
            if not record.clamps_component_ids:
                record.clamps_size_summary = ""
                continue
            
            size_groups = {}
            for component in record.clamps_component_ids:
                size = component.size_specification or 'Unknown'
                if size not in size_groups:
                    size_groups[size] = 0
                size_groups[size] += component.nos
            
            if size_groups:
                summary_parts = []
                for size in sorted(size_groups.keys()):
                    summary_parts.append(f"{size}: {size_groups[size]} pcs")
                record.clamps_size_summary = " | ".join(summary_parts)
            else:
                record.clamps_size_summary = "No clamps configured"
    
    @api.depends('bay_side_border_purlin', 'span_side_border_purlin',
                 'front_bay_asc', 'back_bay_asc', 'front_span_asc', 'back_span_asc',
                 'thick_column', 'no_anchor_frame_lines')
    def _compute_border_purlin_clamps_summary(self):
        """Compute border purlin clamps summary"""
        for record in self:
            if int(record.bay_side_border_purlin or 0) == 0 and \
               int(record.span_side_border_purlin or 0) == 0:
                record.border_purlin_clamps_summary = ""
                continue
            
            summary_parts = []
            
            if int(record.bay_side_border_purlin or 0) > 0:
                bay_info = f"Bay Side: {record.bay_side_border_purlin}"
                if record.front_bay_asc:
                    bay_info += " (Front ASC)"
                if record.back_bay_asc:
                    bay_info += " (Back ASC)"
                summary_parts.append(bay_info)
            
            if int(record.span_side_border_purlin or 0) > 0:
                span_info = f"Span Side: {record.span_side_border_purlin}"
                if record.front_span_asc:
                    span_info += " (Front ASC)"
                if record.back_span_asc:
                    span_info += " (Back ASC)"
                summary_parts.append(span_info)
            
            if hasattr(record, 'thick_column') and record.thick_column != '0':
                thick_label = dict(record._fields['thick_column'].selection).get(
                    record.thick_column, '')
                summary_parts.append(f"Thick: {thick_label}")
            
            if hasattr(record, 'no_anchor_frame_lines') and record.no_anchor_frame_lines > 0:
                summary_parts.append(f"AF Lines: {record.no_anchor_frame_lines}")
            
            record.border_purlin_clamps_summary = " | ".join(summary_parts) if summary_parts else ""
    
    # =============================================
    # VALIDATION
    # =============================================
    
    @api.constrains('big_purlin_clamp_type_first', 'big_purlin_clamp_type_second',
                    'small_purlin_clamp_type_first', 'small_purlin_clamp_type_second')
    def _check_purlin_clamp_configuration(self):
        """Validate purlin clamp configuration"""
        for record in self:
            if record.big_purlin_clamp_type_first and not record.big_purlin_clamp_type_second:
                raise ValidationError(
                    "Big Purlin Second Type cannot be blank when First Type is selected!")
            
            if record.small_purlin_clamp_type_first and not record.small_purlin_clamp_type_second:
                raise ValidationError(
                    "Small Purlin Second Type cannot be blank when First Type is selected!")
    
    # =============================================
    # MAIN CALCULATION METHODS
    # =============================================
    
    def _calculate_all_accessories(self):
        """Extend to add clamp calculations"""
        super()._calculate_all_accessories()
        self._calculate_clamp_components()
    
    def _calculate_clamp_components(self):
        """Calculate all clamp components"""
        self.clamps_component_ids.unlink()
        self._calculate_advanced_clamps()
    
    def _calculate_advanced_clamps(self):
        """Main method for advanced clamp calculations"""
        arch_support_type = getattr(self, 'arch_support_type', 'none')
        
        if (self.clamp_type == 'none' and 
            arch_support_type in ['none', ''] and
            int(self.bay_side_border_purlin or 0) <= 0 and 
            int(self.span_side_border_purlin or 0) <= 0 and
            not (hasattr(self, 'is_side_coridoors') and self.is_side_coridoors) and
            not (hasattr(self, 'is_bottom_chord') and self.is_bottom_chord)):
            _logger.info("No clamps configuration detected, skipping clamp calculations")
            return
        
        clamp_accumulator = {}
        
        # Standard clamp calculations
        if self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(clamp_accumulator)
        elif self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(clamp_accumulator)
        
        if arch_support_type == 'arch_2_bottom':
            self._accumulate_arch_2_bottom_clamps(clamp_accumulator)
        elif arch_support_type == 'arch_2_straight':
            self._accumulate_arch_2_straight_clamps(clamp_accumulator)
        
        self._accumulate_purlin_clamps(clamp_accumulator)
        
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord:
            self._accumulate_v_support_main_column_clamps(clamp_accumulator)
        
        self._accumulate_vent_support_small_arch_clamps(clamp_accumulator)
        self._accumulate_cross_bracing_clamps(clamp_accumulator)
        self._accumulate_border_purlin_clamps(clamp_accumulator)
        
        # ASC Clamps
        if hasattr(self, 'is_side_coridoors') and self.is_side_coridoors:
            self._accumulate_asc_clamps_complete(clamp_accumulator)
        
        self._create_clamp_components_from_accumulator(clamp_accumulator)
    
    # =============================================
    # ASC CLAMPS - FIXED MIDDLE COLUMN SIZE LOGIC
    # =============================================
    
    def _accumulate_asc_clamps_complete(self, accumulator):
        """
        Complete ASC clamp logic based on document specifications
        Handles F Brackets and Gutter Arch Brackets with full configuration
        """
        gutter_bracket_type = getattr(self, 'gutter_bracket_type', 'none')
        
        if gutter_bracket_type == 'f_bracket':
            self._accumulate_asc_clamps_f_bracket(accumulator)
        elif gutter_bracket_type == 'arch':
            self._accumulate_asc_clamps_gutter_arch(accumulator)
        else:
            has_asc = (self.front_span_asc or self.back_span_asc or 
                       self.front_bay_asc or self.back_bay_asc)
            
            if has_asc:
                _logger.warning("⚠️ ASC is enabled but Gutter Bracket Type is 'None'. "
                               "Calculating clamps for ALL present ASC sides (conservative approach).")
                self._accumulate_asc_clamps_default(accumulator)
    
    def _accumulate_asc_clamps_f_bracket(self, accumulator):
        """ASC Clamps for F Brackets - FIXED to use correct middle column size"""
        _logger.info("=== ASC CLAMPS: F BRACKET MODE ===")
        
        thick_column = getattr(self, 'thick_column', '0')
        no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        no_middle_columns_per_af = int(getattr(self, 'no_column_big_frame', 0))  # This is actually middle columns per AF
        
        # FRONT SPAN ASC
        if self.front_span_asc:
            _logger.info("Processing Front Span ASC (F Bracket)")
            
            if thick_column in ['1', '2']:  # 4 Corner or 2 Bay Side
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"  Front Span: 2 × Full Clamp - {thick_size} (Thick)")
                
                if no_anchor_frame_lines >= 1:
                    # FIXED: Using middle column size for middle columns
                    middle_size = self._get_middle_column_pipe_size()
                    if middle_size and no_middle_columns_per_af > 0:
                        qty = self.no_of_spans * no_middle_columns_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                    
                    af_main_size = self._get_af_column_pipe_size()
                    if af_main_size:
                        qty = self.no_of_spans - 1
                        if qty > 0:
                            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                            _logger.info(f"  Front Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
                else:
                    main_size = self._get_main_column_pipe_size()
                    if main_size:
                        qty = self.no_of_spans - 1
                        if qty > 0:
                            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                            _logger.info(f"  Front Span: {qty} × Full Clamp - {main_size} (Main)")
            
            elif thick_column in ['3', '4']:  # 2 Span Side or All 4 Side
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                    _logger.info(f"  Front Span: {qty} × Full Clamp - {thick_size} (Thick)")
                
                if no_anchor_frame_lines >= 1:
                    # FIXED: Using middle column size for middle columns
                    middle_size = self._get_middle_column_pipe_size()
                    if middle_size and no_middle_columns_per_af > 0:
                        qty = self.no_of_spans * no_middle_columns_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
            
            else:  # thick_column == '0'
                if no_anchor_frame_lines > 0:
                    # FIXED: Using middle column size for middle columns
                    middle_size = self._get_middle_column_pipe_size()
                    if middle_size and no_middle_columns_per_af > 0:
                        qty = self.no_of_spans * no_middle_columns_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                    
                    af_main_size = self._get_af_column_pipe_size()
                    if af_main_size:
                        qty = self.no_of_spans + 1
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
                else:
                    main_size = self._get_main_column_pipe_size()
                    if main_size:
                        qty = self.no_of_spans + 1
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {main_size} (Main)")
        
        # BACK SPAN ASC
        if self.back_span_asc:
            _logger.info("Processing Back Span ASC (F Bracket)")
            
            if thick_column in ['1', '2']:  # 4 Corner or 2 Bay Side
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"  Back Span: 2 × Full Clamp - {thick_size} (Thick)")
                
                if no_anchor_frame_lines >= 2:
                    # FIXED: Using middle column size for middle columns
                    middle_size = self._get_middle_column_pipe_size()
                    if middle_size and no_middle_columns_per_af > 0:
                        qty = self.no_of_spans * no_middle_columns_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                        _logger.info(f"  Back Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                    
                    af_main_size = self._get_af_column_pipe_size()
                    if af_main_size:
                        qty = self.no_of_spans - 1
                        if qty > 0:
                            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                            _logger.info(f"  Back Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
                else:
                    main_size = self._get_main_column_pipe_size()
                    if main_size:
                        qty = self.no_of_spans - 1
                        if qty > 0:
                            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                            _logger.info(f"  Back Span: {qty} × Full Clamp - {main_size} (Main)")
            
            elif thick_column in ['3', '4']:  # 2 Span Side or All 4 Side
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                    _logger.info(f"  Back Span: {qty} × Full Clamp - {thick_size} (Thick)")
                
                if no_anchor_frame_lines > 1:
                    # FIXED: Using middle column size for middle columns
                    middle_size = self._get_middle_column_pipe_size()
                    if middle_size and no_middle_columns_per_af > 0:
                        qty = self.no_of_spans * no_middle_columns_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                        _logger.info(f"  Back Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
            
            else:  # thick_column == '0'
                if no_anchor_frame_lines > 1:
                    # FIXED: Using middle column size for middle columns
                    middle_size = self._get_middle_column_pipe_size()
                    if middle_size and no_middle_columns_per_af > 0:
                        qty = self.no_of_spans * no_middle_columns_per_af
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                        _logger.info(f"  Back Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                    
                    af_main_size = self._get_af_column_pipe_size()
                    if af_main_size:
                        qty = self.no_of_spans + 1
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                        _logger.info(f"  Back Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
                else:
                    main_size = self._get_main_column_pipe_size()
                    if main_size:
                        qty = self.no_of_spans + 1
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"  Back Span: {qty} × Full Clamp - {main_size} (Main)")
        
        # FRONT BAY ASC (F Bracket mode)
        if self.front_bay_asc:
            _logger.info("Processing Front Bay ASC (F Bracket)")
            self._process_bay_asc_f_bracket(accumulator, 'front', thick_column, no_anchor_frame_lines)
        
        # BACK BAY ASC (F Bracket mode)
        if self.back_bay_asc:
            _logger.info("Processing Back Bay ASC (F Bracket)")
            self._process_bay_asc_f_bracket(accumulator, 'back', thick_column, no_anchor_frame_lines)
    
    def _accumulate_asc_clamps_f_bracket_span_logic(self, accumulator, side, af_check):
        """Reusable span logic for F Bracket and Gutter Arch - FIXED for middle column size"""
        thick_column = getattr(self, 'thick_column', '0')
        no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        no_middle_columns_per_af = int(getattr(self, 'no_column_big_frame', 0))  # This is actually middle columns per AF
        side_label = side.title()
        
        _logger.info(f"Processing {side_label} Span ASC")
        
        if thick_column in ['1', '2']:  # 4 Corner or 2 Bay Side
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"  {side_label} Span: 2 × Full Clamp - {thick_size} (Thick)")
            
            if no_anchor_frame_lines >= af_check:
                # FIXED: Using middle column size for middle columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and no_middle_columns_per_af > 0:
                    qty = self.no_of_spans * no_middle_columns_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                
                af_main_size = self._get_af_column_pipe_size()
                if af_main_size:
                    qty = self.no_of_spans - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                        _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_spans - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['3', '4']:  # 2 Span Side or All 4 Side
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                qty = self.no_of_spans + 1
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {thick_size} (Thick)")
            
            if no_anchor_frame_lines >= af_check:
                # FIXED: Using middle column size for middle columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and no_middle_columns_per_af > 0:
                    qty = self.no_of_spans * no_middle_columns_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
        
        else:  # thick_column == '0'
            if no_anchor_frame_lines >= af_check:
                # FIXED: Using middle column size for middle columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and no_middle_columns_per_af > 0:
                    qty = self.no_of_spans * no_middle_columns_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                
                af_main_size = self._get_af_column_pipe_size()
                if af_main_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {main_size} (Main)")
    
    def _process_bay_asc_f_bracket(self, accumulator, side, thick_column, af_lines):
        """Process Bay ASC for F Bracket mode"""
        side_label = side.title()
        
        if thick_column in ['1', '3']:  # 4 Corner or 2 Span Side
            if af_lines < 3:
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"  {side_label} Bay: 2 × Full Clamp - {thick_size} (Thick)")
                
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_bays - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {main_size} (Main)")
            else:
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"  {side_label} Bay: 2 × Full Clamp - {thick_size} (Thick)")
                
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    qty_af = af_lines - 2
                    if qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                        _logger.info(f"  {side_label} Bay: {qty_af} × Full Clamp - {af_size} (AF)")
                
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty_main = (self.no_of_bays + 1) - af_lines
                    if qty_main > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                        _logger.info(f"  {side_label} Bay: {qty_main} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['2', '4']:  # 2 Bay Side or All 4 Side
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                qty = self.no_of_bays + 1
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {thick_size} (Thick)")
        
        else:  # thick_column == '0'
            if af_lines == 0:
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_bays + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {main_size} (Main)")
            else:
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_lines)
                    _logger.info(f"  {side_label} Bay: {af_lines} × Full Clamp - {af_size} (AF)")
                
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = (self.no_of_bays + 1) - af_lines
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {main_size} (Main)")
    
    def _accumulate_asc_clamps_gutter_arch(self, accumulator):
        """ASC Clamps for Gutter Arch Brackets"""
        bay_side_required = getattr(self, 'bay_side_clamp_required', False)
        
        _logger.info(f"=== ASC CLAMPS: GUTTER ARCH BRACKET MODE (Bay Side Required: {bay_side_required}) ===")
        
        # Process span sides (same logic as F Bracket)
        if self.front_span_asc:
            self._accumulate_asc_clamps_f_bracket_span_logic(accumulator, 'front', 1)
        
        if self.back_span_asc:
            self._accumulate_asc_clamps_f_bracket_span_logic(accumulator, 'back', 2)
        
        # Process bay sides only if required
        if bay_side_required:
            thick_column = getattr(self, 'thick_column', '0')
            no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
            
            if self.front_bay_asc:
                _logger.info("Processing Front Bay ASC (Gutter Arch - Bay Side Required)")
                self._process_bay_asc_f_bracket(accumulator, 'front', thick_column, no_anchor_frame_lines)
            
            if self.back_bay_asc:
                _logger.info("Processing Back Bay ASC (Gutter Arch - Bay Side Required)")
                self._process_bay_asc_f_bracket(accumulator, 'back', thick_column, no_anchor_frame_lines)
    
    def _accumulate_asc_clamps_default(self, accumulator):
        """ASC Clamps when no bracket type is selected - use F Bracket logic for all sides"""
        _logger.info("=== ASC CLAMPS: DEFAULT MODE (Using F Bracket logic for all sides) ===")
        self._accumulate_asc_clamps_f_bracket(accumulator)
        
    # =============================================
    # BORDER PURLIN CLAMPS - COMPLETE SPECIFICATION IMPLEMENTATION
    # =============================================
    
    def _accumulate_border_purlin_clamps(self, accumulator):
        """
        Accumulate border purlin clamps with FULL specification support
        Implements complete logic from Border Purlin Clamps specification document
        """
        if int(self.bay_side_border_purlin or 0) > 0:
            self._calculate_bay_side_border_clamps_spec(accumulator)
        
        if int(self.span_side_border_purlin or 0) > 0:
            self._calculate_span_side_border_clamps_spec(accumulator)
    
    def _calculate_bay_side_border_clamps_spec(self, accumulator):
        """
        SPECIFICATION IMPLEMENTATION: Bay Side Border Purlin Clamps
        Handles Front Bay and Back Bay with full logic tree
        """
        bay_side_border_purlin = int(self.bay_side_border_purlin)
        thick_column = getattr(self, 'thick_column', '0')
        no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        
        _logger.info(f"=== BAY SIDE BORDER PURLIN CLAMPS (Spec Implementation) ===")
        _logger.info(f"Bay Side Border Purlin: {bay_side_border_purlin}")
        _logger.info(f"Thick Column: {thick_column}")
        _logger.info(f"AF Lines: {no_anchor_frame_lines}")
        
        # FRONT BAY
        if hasattr(self, 'front_bay_asc') and self.front_bay_asc:
            _logger.info("Front Bay: ASC Present")
            self._add_bay_border_clamps_with_asc(accumulator, bay_side_border_purlin, 'Front Bay')
        else:
            _logger.info("Front Bay: No ASC")
            self._add_bay_border_clamps_without_asc(accumulator, bay_side_border_purlin, 
                                                    thick_column, no_anchor_frame_lines, 'Front Bay')
        
        # BACK BAY
        if hasattr(self, 'back_bay_asc') and self.back_bay_asc:
            _logger.info("Back Bay: ASC Present")
            self._add_bay_border_clamps_with_asc(accumulator, bay_side_border_purlin, 'Back Bay')
        else:
            _logger.info("Back Bay: No ASC")
            self._add_bay_border_clamps_without_asc(accumulator, bay_side_border_purlin, 
                                                    thick_column, no_anchor_frame_lines, 'Back Bay')
    
    def _add_bay_border_clamps_with_asc(self, accumulator, bay_side_border_purlin, side_label):
        """Bay side clamps when ASC is present"""
        asc_size = self._get_asc_pipe_size()
        if not asc_size:
            _logger.warning(f"{side_label} ASC enabled but pipe size not found")
            return
        
        # Half Clamps
        half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
            _logger.info(f"  {side_label}: {half_qty} × Half Clamp - {asc_size}")
        
        # Full Clamps
        full_qty = 2 * bay_side_border_purlin
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)
            _logger.info(f"  {side_label}: {full_qty} × Full Clamp - {asc_size}")
    
    def _add_bay_border_clamps_without_asc(self, accumulator, bay_side_border_purlin, 
                                           thick_column, af_lines, side_label):
        """Bay side clamps when NO ASC - Full specification logic"""
        
        if thick_column == '1':  # 4 Corner
            _logger.info(f"  {side_label}: Thick Column = 4 Corner")
            
            if af_lines in [0, 1, 2]:
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                        _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                
                # Full Clamps: Thick Column
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    full_qty = 2 * bay_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                        _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
            
            else:  # AF Lines > 2
                # Half Clamps: AF Column
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    half_qty_af = (af_lines - 2) * bay_side_border_purlin
                    if half_qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                        _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
                
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty_main = (self.no_of_bays - 1 - (af_lines - 2)) * bay_side_border_purlin
                    if half_qty_main > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty_main)
                        _logger.info(f"    Half Clamps (Main): {half_qty_main} × {main_size}")
                
                # Full Clamps: Thick Column
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    full_qty = 2 * bay_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                        _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        elif thick_column in ['2', '4']:  # 2 Bay Side / All 4 Side
            _logger.info(f"  {side_label}: Thick Column = 2 Bay Side or All 4 Side")
            
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                # Half Clamps: Thick Column
                half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_size, half_qty)
                    _logger.info(f"    Half Clamps (Thick): {half_qty} × {thick_size}")
                
                # Full Clamps: Thick Column
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        else:  # thick_column == '0' or '3' (No Thick / 2 Span Side)
            _logger.info(f"  {side_label}: Thick Column = None or 2 Span Side")
            
            if af_lines == 0:
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                        _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                
                # Full Clamps: Main Column
                if main_size:
                    full_qty = 2 * bay_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, full_qty)
                        _logger.info(f"    Full Clamps (Main): {full_qty} × {main_size}")
            
            elif af_lines == 1:
                # Full Clamps: AF Column
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    full_qty_af = bay_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty_af)
                    _logger.info(f"    Full Clamps (AF): {full_qty_af} × {af_size}")
                
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                        _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                
                # Full Clamps: Main Column
                if main_size:
                    full_qty = bay_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, full_qty)
                    _logger.info(f"    Full Clamps (Main): {full_qty} × {main_size}")
            
            elif af_lines == 2:
                # Full Clamps: AF Column
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    full_qty_af = 2 * bay_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty_af)
                    _logger.info(f"    Full Clamps (AF): {full_qty_af} × {af_size}")
                
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                        _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
            
            else:  # AF Lines > 2
                # Full Clamps: AF Column
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    full_qty_af = 2 * bay_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty_af)
                    _logger.info(f"    Full Clamps (AF): {full_qty_af} × {af_size}")
                
                # Half Clamps: AF Column
                if af_size:
                    half_qty_af = (af_lines - 2) * bay_side_border_purlin
                    if half_qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                        _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
                
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty_main = (self.no_of_bays - af_lines + 1) * bay_side_border_purlin
                    if half_qty_main > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty_main)
                        _logger.info(f"    Half Clamps (Main): {half_qty_main} × {main_size}")
    
    def _calculate_span_side_border_clamps_spec(self, accumulator):
        """
        SPECIFICATION IMPLEMENTATION: Span Side Border Purlin Clamps
        Handles Front Span and Back Span with full logic tree
        """
        span_side_border_purlin = int(self.span_side_border_purlin)
        thick_column = getattr(self, 'thick_column', '0')
        no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        
        _logger.info(f"=== SPAN SIDE BORDER PURLIN CLAMPS (Spec Implementation) ===")
        _logger.info(f"Span Side Border Purlin: {span_side_border_purlin}")
        _logger.info(f"Thick Column: {thick_column}")
        _logger.info(f"AF Lines: {no_anchor_frame_lines}")
        
        # FRONT SPAN
        if hasattr(self, 'front_span_asc') and self.front_span_asc:
            _logger.info("Front Span: ASC Present")
            self._add_span_border_clamps_with_asc(accumulator, span_side_border_purlin, 'Front Span')
        else:
            _logger.info("Front Span: No ASC")
            self._add_span_border_clamps_without_asc(accumulator, span_side_border_purlin, 
                                                     thick_column, no_anchor_frame_lines, 'Front Span')
        
        # BACK SPAN
        if hasattr(self, 'back_span_asc') and self.back_span_asc:
            _logger.info("Back Span: ASC Present")
            self._add_span_border_clamps_with_asc(accumulator, span_side_border_purlin, 'Back Span')
        else:
            _logger.info("Back Span: No ASC")
            self._add_span_border_clamps_without_asc(accumulator, span_side_border_purlin, 
                                                     thick_column, no_anchor_frame_lines, 'Back Span')
    
    def _add_span_border_clamps_with_asc(self, accumulator, span_side_border_purlin, side_label):
        """Span side clamps when ASC is present"""
        asc_size = self._get_asc_pipe_size()
        if not asc_size:
            _logger.warning(f"{side_label} ASC enabled but pipe size not found")
            return
        
        # Half Clamps
        half_qty = (self.no_of_spans - 1) * span_side_border_purlin
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
            _logger.info(f"  {side_label}: {half_qty} × Half Clamp - {asc_size}")
        
        # Full Clamps
        full_qty = 2 * span_side_border_purlin
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)
            _logger.info(f"  {side_label}: {full_qty} × Full Clamp - {asc_size}")
    
    def _add_span_border_clamps_without_asc(self, accumulator, span_side_border_purlin, 
                                            thick_column, af_lines, side_label):
        """Span side clamps when NO ASC - Full specification logic"""
        
        if thick_column == '1':  # 4 Corner
            _logger.info(f"  {side_label}: Thick Column = 4 Corner")
            
            if af_lines == 0:
                # Half Clamps: Main Column
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    half_qty = (self.no_of_spans - 1) * span_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                        _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                
                # Full Clamps: Thick Column
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    full_qty = 2 * span_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                        _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
            
            elif af_lines > 0:
                # Half Clamps: AF Column
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    half_qty_af = (self.no_of_spans - 1) * span_side_border_purlin
                    if half_qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                        _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
                
                # Half Clamps: Middle Column
                middle_size = self._get_middle_column_pipe_size()
                if middle_size:
                    half_qty_middle = self.no_of_spans * span_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                    _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
                
                # Full Clamps: Thick Column
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    full_qty = 2 * span_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                        _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        elif thick_column in ['3', '4']:  # 2 Span Side / All 4 Side
            _logger.info(f"  {side_label}: Thick Column = 2 Span Side or All 4 Side")
            
            if af_lines == 0:
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    # Half Clamps: Thick Column
                    half_qty = (self.no_of_spans - 1) * span_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_size, half_qty)
                        _logger.info(f"    Half Clamps (Thick): {half_qty} × {thick_size}")
                    
                    # Full Clamps: Thick Column
                    full_qty = 2 * span_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                        _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
            
            else:  # AF Lines > 0
                # Half Clamps: Thick Column
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    half_qty_thick = (self.no_of_spans - 1) * span_side_border_purlin
                    if half_qty_thick > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_size, half_qty_thick)
                        _logger.info(f"    Half Clamps (Thick): {half_qty_thick} × {thick_size}")
                
                # Half Clamps: Middle Column
                middle_size = self._get_middle_column_pipe_size()
                if middle_size:
                    half_qty_middle = self.no_of_spans * span_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                    _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
                
                # Full Clamps: Thick Column
                if thick_size:
                    full_qty = 2 * span_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                        _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        else:  # thick_column == '0' or '2' (No Thick / 2 Bay Side)
            _logger.info(f"  {side_label}: Thick Column = None or 2 Bay Side")
            
            if af_lines == 0:
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    # Half Clamps: Main Column
                    half_qty = (self.no_of_spans - 1) * span_side_border_purlin
                    if half_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                        _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                    
                    # Full Clamps: Main Column
                    full_qty = 2 * span_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, full_qty)
                        _logger.info(f"    Full Clamps (Main): {full_qty} × {main_size}")
            
            else:  # AF Lines > 0
                # Half Clamps: AF Column
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    half_qty_af = (self.no_of_spans - 1) * span_side_border_purlin
                    if half_qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                        _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
                
                # Half Clamps: Middle Column
                middle_size = self._get_middle_column_pipe_size()
                if middle_size:
                    half_qty_middle = self.no_of_spans * span_side_border_purlin
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                    _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
                
                # Full Clamps: AF Column
                if af_size:
                    full_qty = 2 * span_side_border_purlin
                    if full_qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty)
                        _logger.info(f"    Full Clamps (AF): {full_qty} × {af_size}")
    
    # =============================================
    # VENT SUPPORT SMALL ARCH CLAMPS
    # =============================================
    
    def _accumulate_vent_support_small_arch_clamps(self, accumulator):
        """Accumulate clamps for Vent Support for Small Arch"""
        vent_small_support = self.truss_component_ids.filtered(
            lambda c: c.name == 'Vent Support for Small Arch')
        
        if not vent_small_support or vent_small_support.nos == 0:
            return
        
        vent_count = vent_small_support.nos
        _logger.info(f"=== VENT SUPPORT SMALL ARCH CLAMPS ===")
        _logger.info(f"Vent Support count: {vent_count}")
        
        # Full Clamps - Bottom Chord
        bottom_chord_data = self._get_bottom_chord_data()
        if bottom_chord_data['size']:
            qty = vent_count // 2
            if qty > 0:
                self._add_to_clamp_accumulator(
                    accumulator, 'Full Clamp', 
                    bottom_chord_data['size'], qty
                )
                _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
        
        # Full Clamps - Small Arch Purlin (using purlin size, not arch size)
        small_arch_purlin_size = self._get_small_arch_purlin_size()
        if small_arch_purlin_size:
            self._add_to_clamp_accumulator(
                accumulator, 'Full Clamp', 
                small_arch_purlin_size, vent_count
            )
            _logger.info(f"  {vent_count} × Full Clamp - {small_arch_purlin_size} (Small Arch Purlin)")
    
    # =============================================
    # CROSS BRACING CLAMPS
    # =============================================
    
    def _accumulate_cross_bracing_clamps(self, accumulator):
        """
        Accumulate Front & Back Column to Column Cross Bracing X Clamps
        Handles AFX lines logic
        """
        cross_bracing = self.lower_component_ids.filtered(
            lambda c: c.name == 'Front & Back Column to Column Cross Bracing X'
        )
        
        if not cross_bracing or cross_bracing.nos == 0:
            return
        
        cross_bracing_count = cross_bracing.nos
        af_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        thick_column = getattr(self, 'thick_column', '0')
        
        _logger.info(f"=== CROSS BRACING CLAMPS ===")
        _logger.info(f"Cross Bracing count: {cross_bracing_count}")
        _logger.info(f"AF Lines: {af_lines}, Thick Column: {thick_column}")
        
        # Calculate AFX (max 4)
        afx = 0
        if af_lines > 2:
            afx = min(af_lines - 2, 4)
            _logger.info(f"AFX calculated as {afx} (AF Lines: {af_lines})")
        
        main_size = self._get_main_column_pipe_size()
        af_size = self._get_af_column_pipe_size()
        thick_size = self._get_thick_column_pipe_size()
        
        if thick_column in ['1', '3', '0']:  # 4 Corner / 2 Span Side / 0 Thick
            if afx == 0:
                if main_size:
                    qty = cross_bracing_count * 2
                    self._add_to_clamp_accumulator(
                        accumulator, 'Full Clamp', main_size, qty
                    )
                    _logger.info(f"  {qty} × Full Clamp - {main_size} (Main)")
            else:
                if af_size:
                    qty_af = afx * 2 * (self.no_of_spans + 1)
                    self._add_to_clamp_accumulator(
                        accumulator, 'Full Clamp', af_size, qty_af
                    )
                    _logger.info(f"  {qty_af} × Full Clamp - {af_size} (AF)")
                
                if main_size:
                    qty_main = (cross_bracing_count * 2) - (afx * 2 * (self.no_of_spans + 1))
                    if qty_main > 0:
                        self._add_to_clamp_accumulator(
                            accumulator, 'Full Clamp', main_size, qty_main
                        )
                        _logger.info(f"  {qty_main} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['2', '4']:  # 2 Bay Side / All 4 Side
            if afx == 0:
                if thick_size:
                    self._add_to_clamp_accumulator(
                        accumulator, 'Full Clamp', thick_size, 16
                    )
                    _logger.info(f"  16 × Full Clamp - {thick_size} (Thick)")
                
                if main_size:
                    qty = (cross_bracing_count * 2) - 16
                    if qty > 0:
                        self._add_to_clamp_accumulator(
                            accumulator, 'Full Clamp', main_size, qty
                        )
                        _logger.info(f"  {qty} × Full Clamp - {main_size} (Main)")
            else:
                if thick_size:
                    self._add_to_clamp_accumulator(
                        accumulator, 'Full Clamp', thick_size, 16
                    )
                    _logger.info(f"  16 × Full Clamp - {thick_size} (Thick)")
                
                if af_size:
                    qty_af = afx * 2 * (self.no_of_spans + 1)
                    self._add_to_clamp_accumulator(
                        accumulator, 'Full Clamp', af_size, qty_af
                    )
                    _logger.info(f"  {qty_af} × Full Clamp - {af_size} (AF)")
                
                if main_size:
                    qty_main = (cross_bracing_count * 2) - (afx * 2 * (self.no_of_spans + 1)) - 16
                    if qty_main > 0:
                        self._add_to_clamp_accumulator(
                            accumulator, 'Full Clamp', main_size, qty_main
                        )
                        _logger.info(f"  {qty_main} × Full Clamp - {main_size} (Main)")
                  
                 
    # =============================================
    # STANDARD CLAMP METHODS
    # =============================================
    
    def _accumulate_w_type_clamps(self, accumulator):
        """Accumulate W Type clamps"""
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_big_support_count = self._get_vent_big_support_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        
        _logger.info("=== W TYPE CLAMPS ===")
        
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
            _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
        
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_big_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
            _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
        
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], 
                                          small_arch_data['count'])
            _logger.info(f"  {small_arch_data['count']} × Full Clamp - {small_arch_data['size']} (Small Arch)")
        
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                          arch_support_straight_middle_data['size'], 
                                          arch_support_straight_middle_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', 
                                          arch_support_straight_middle_data['size'], 
                                          arch_support_straight_middle_data['count'])
            _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                        f"{arch_support_straight_middle_data['size']} (Arch Support Straight Middle)")
            _logger.info(f"  {arch_support_straight_middle_data['count']} × Half Clamp - "
                        f"{arch_support_straight_middle_data['size']} (Arch Support Straight Middle)")
        
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
            _logger.info(f"  {middle_column_data['count']} × Full Clamp - {middle_column_data['size']} (Middle Column)")
            _logger.info(f"  {middle_column_data['count']} × Half Clamp - {middle_column_data['size']} (Middle Column)")
    
    def _accumulate_m_type_clamps(self, accumulator):
        """Accumulate M Type clamps"""
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_big_support_count = self._get_vent_big_support_count()
        middle_column_data = self._get_middle_column_data()
        
        _logger.info(f"=== M TYPE CLAMPS (Bottom Chord Type: {self.bottom_chord_clamp_type}) ===")
        
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            if self.bottom_chord_clamp_type == 'single':
                qty = (bottom_chord_data['count'] * 3) + v_support_count
            else:  # triple
                qty = (bottom_chord_data['count'] * 5) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
            _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
        
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_big_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
            _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
        
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], 
                                          small_arch_data['count'])
            _logger.info(f"  {small_arch_data['count']} × Full Clamp - {small_arch_data['size']} (Small Arch)")
        
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
            _logger.info(f"  {middle_column_data['count']} × Full Clamp - {middle_column_data['size']} (Middle Column)")
            _logger.info(f"  {middle_column_data['count']} × Half Clamp - {middle_column_data['size']} (Middle Column)")
    
    def _accumulate_arch_2_bottom_clamps(self, accumulator):
        """Accumulate clamps for Arch to Bottom Support"""
        bottom_chord_data = self._get_bottom_chord_data()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        small_arch_support_count = self._get_small_arch_support_count()
        
        _logger.info("=== ARCH TO BOTTOM CLAMPS ===")
        
        if small_arch_support_count > 0:
            if bottom_chord_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              bottom_chord_data['size'], small_arch_support_count)
                _logger.info(f"  {small_arch_support_count} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
            if big_arch_data['size']:
                qty = small_arch_support_count // 2
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                                  big_arch_data['size'], qty)
                    _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
            if small_arch_data['size']:
                qty = small_arch_support_count // 2
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                                  small_arch_data['size'], qty)
                    _logger.info(f"  {qty} × Full Clamp - {small_arch_data['size']} (Small Arch)")
        
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        if arch_support_straight_middle_data['count'] > 0:
            if bottom_chord_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              bottom_chord_data['size'], 
                                              arch_support_straight_middle_data['count'])
                _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                            f"{bottom_chord_data['size']} (Bottom Chord for Straight Middle)")
            if big_arch_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              big_arch_data['size'], 
                                              arch_support_straight_middle_data['count'])
                _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                            f"{big_arch_data['size']} (Big Arch for Straight Middle)")
    
    def _accumulate_arch_2_straight_clamps(self, accumulator):
        """Accumulate clamps for Arch to Straight Middle"""
        bottom_chord_data = self._get_bottom_chord_data()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        big_arch_support_count = self._get_big_arch_support_count()
        
        _logger.info("=== ARCH TO STRAIGHT MIDDLE CLAMPS ===")
        
        if big_arch_support_count > 0:
            if bottom_chord_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              bottom_chord_data['size'], big_arch_support_count)
                _logger.info(f"  {big_arch_support_count} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
            if big_arch_data['size']:
                qty = big_arch_support_count // 2
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                                  big_arch_data['size'], qty)
                    _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
            if small_arch_data['size']:
                qty = big_arch_support_count // 2
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                                  small_arch_data['size'], qty)
                    _logger.info(f"  {qty} × Full Clamp - {small_arch_data['size']} (Small Arch)")
        
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        if arch_support_straight_middle_data['count'] > 0 and big_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                          big_arch_data['size'], 
                                          arch_support_straight_middle_data['count'])
            _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                        f"{big_arch_data['size']} (Big Arch for Straight Middle)")
    
    def _accumulate_purlin_clamps(self, accumulator):
        """Accumulate purlin clamps"""
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        
        _logger.info("=== PURLIN CLAMPS ===")
        
        # Big Arch Purlin Clamps
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            if self.big_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                clamp_name = 'Full Clamp' if self.big_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
                self._add_to_clamp_accumulator_separate(
                    accumulator, f"{clamp_name} (Big Arch Purlin)", big_arch_data['size'], qty_first)
                _logger.info(f"  {qty_first} × {clamp_name} - {big_arch_data['size']} (Big Arch Purlin First)")
                
                if self.big_purlin_clamp_type_second:
                    qty_second = big_arch_data['count'] - qty_first
                    if qty_second > 0:
                        clamp_name = ('Half Clamp' if self.big_purlin_clamp_type_second == 'half_clamp' 
                                     else 'T Joint')
                        self._add_to_clamp_accumulator_separate(
                            accumulator, f"{clamp_name} (Big Arch Purlin)", big_arch_data['size'], qty_second)
                        _logger.info(f"  {qty_second} × {clamp_name} - {big_arch_data['size']} (Big Arch Purlin Second)")
        
        # Small Arch Purlin Clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            if self.small_purlin_clamp_type_first:
                qty_first = self.no_of_spans * 2
                clamp_name = ('Full Clamp' if self.small_purlin_clamp_type_first == 'full_clamp' 
                             else 'L Joint')
                self._add_to_clamp_accumulator_separate(
                    accumulator, f"{clamp_name} (Small Arch Purlin)", small_arch_data['size'], qty_first)
                _logger.info(f"  {qty_first} × {clamp_name} - {small_arch_data['size']} (Small Arch Purlin First)")
                
                if self.small_purlin_clamp_type_second:
                    qty_second = small_arch_data['count'] - qty_first
                    if qty_second > 0:
                        clamp_name = ('Half Clamp' if self.small_purlin_clamp_type_second == 'half_clamp' 
                                     else 'T Joint')
                        self._add_to_clamp_accumulator_separate(
                            accumulator, f"{clamp_name} (Small Arch Purlin)", small_arch_data['size'], qty_second)
                        _logger.info(f"  {qty_second} × {clamp_name} - {small_arch_data['size']} (Small Arch Purlin Second)")
    
    def _accumulate_v_support_main_column_clamps(self, accumulator):
        """Accumulate V Support clamps"""
        v_support_count = self._get_v_support_count()
        if v_support_count == 0:
            return
        
        thick_column = getattr(self, 'thick_column', '0')
        no_anchor_frame_lines = getattr(self, 'no_anchor_frame_lines', 0)
        v_support_frames = int(getattr(self, 'v_support_bottom_chord_frame', 0))
        
        if v_support_frames == 0:
            _logger.warning("V Support count exists but v_support_bottom_chord_frame is 0")
            return
        
        _logger.info(f"=== V SUPPORT MAIN COLUMN CLAMPS ===")
        _logger.info(f"V Support count: {v_support_count}, Frames: {v_support_frames}")
        _logger.info(f"Thick Column: {thick_column}, AF Lines: {no_anchor_frame_lines}")
        
        column_counts = self._get_actual_column_counts()
        
        v_support_distribution = self._calculate_v_support_column_distribution(
            v_support_count,
            v_support_frames,
            thick_column,
            no_anchor_frame_lines,
            column_counts
        )
        
        for column_type, data in v_support_distribution.items():
            if data['count'] > 0 and data['size']:
                self._add_to_clamp_accumulator(
                    accumulator, 
                    'Full Clamp', 
                    data['size'], 
                    data['count']
                )
                _logger.info(f"  {data['count']} × Full Clamp - {data['size']} ({column_type})")
    
    def _get_actual_column_counts(self):
        """Get actual column counts from frame_component_ids"""
        counts = {
            'main': 0,
            'af_main': 0,
            'thick': 0,
            'middle': 0,
            'quadruple': 0
        }
        
        if not hasattr(self, 'frame_component_ids'):
            return counts
        
        for component in self.frame_component_ids:
            if component.name == 'Main Columns':
                counts['main'] = component.nos
            elif component.name == 'AF Main Columns':
                counts['af_main'] = component.nos
            elif component.name == 'Thick Columns':
                counts['thick'] = component.nos
            elif component.name == 'Middle Columns':
                counts['middle'] = component.nos
            elif component.name == 'Quadruple Columns':
                counts['quadruple'] = component.nos
        
        return counts

    def _calculate_v_support_column_distribution(self, total_v_supports, v_support_frames, 
                                                 thick_column, af_lines, column_counts):
        """Calculate V Support distribution across column types"""
        distribution = {
            'thick': {'count': 0, 'size': self._get_thick_column_pipe_size()},
            'af': {'count': 0, 'size': self._get_af_support_column_pipe_size()},  # This is correct for V Support
            'main': {'count': 0, 'size': self._get_main_column_pipe_size()}
        }
        
        v_supports_per_line = total_v_supports // v_support_frames if v_support_frames > 0 else 0
        
        if v_supports_per_line == 0:
            _logger.warning("V supports per line is 0")
            return distribution
        
        columns_per_frame = self.no_of_spans + 1
        
        if thick_column == '0':  # No thick columns
            self._distribute_v_supports_no_thick(
                distribution, v_support_frames, v_supports_per_line, 
                af_lines, columns_per_frame, column_counts
            )
        elif thick_column == '1':  # 4 Corners
            self._distribute_v_supports_4_corners(
                distribution, v_support_frames, v_supports_per_line,
                af_lines, columns_per_frame, column_counts
            )
        elif thick_column == '2':  # 2 Bay Side
            self._distribute_v_supports_bay_side(
                distribution, v_support_frames, v_supports_per_line,
                af_lines, columns_per_frame, column_counts
            )
        elif thick_column == '3':  # 2 Span Side
            self._distribute_v_supports_span_side(
                distribution, v_support_frames, v_supports_per_line,
                af_lines, columns_per_frame, column_counts
            )
        elif thick_column == '4':  # All 4 Side
            self._distribute_v_supports_all_4_side(
                distribution, v_support_frames, v_supports_per_line,
                columns_per_frame
            )
        
        # Verify totals match
        calculated_total = sum(d['count'] for d in distribution.values())
        if calculated_total != total_v_supports:
            _logger.warning(f"V Support distribution mismatch: calculated {calculated_total}, expected {total_v_supports}")
            difference = total_v_supports - calculated_total
            distribution['main']['count'] += difference
        
        return distribution

    def _distribute_v_supports_no_thick(self, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
        """Distribute V Supports when thick_column = '0' (No thick columns)"""
        if af_lines > 0 and col_counts['af_main'] > 0:
            # Some frames have AF columns
            af_frame_ratio = min(af_lines / v_frames, 1.0)
            af_v_supports = int(af_frame_ratio * v_frames * v_per_line)
            
            dist['af']['count'] = af_v_supports
            dist['main']['count'] = (v_frames * v_per_line) - af_v_supports
        else:
            # All frames use main columns
            dist['main']['count'] = v_frames * v_per_line

    def _distribute_v_supports_4_corners(self, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
        """Distribute V Supports when thick_column = '1' (4 Corners)"""
        if v_frames >= 2:
            # Thick columns on first and last frames (corners)
            thick_per_end_frame = min(2, v_per_line)
            dist['thick']['count'] = 2 * thick_per_end_frame
            
            remaining = (v_frames * v_per_line) - dist['thick']['count']
            
            if af_lines > 0 and col_counts['af_main'] > 0:
                af_ratio = min(af_lines / v_frames, 0.5)
                dist['af']['count'] = int(af_ratio * remaining)
                dist['main']['count'] = remaining - dist['af']['count']
            else:
                dist['main']['count'] = remaining
        else:
            # Only one frame, use thick columns for corners
            dist['thick']['count'] = min(2, v_per_line)
            dist['main']['count'] = v_per_line - dist['thick']['count']

    def _distribute_v_supports_bay_side(self, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
        """Distribute V Supports when thick_column = '2' (Both Bay Side)"""
        # Thick columns on all frames, but only for bay side positions
        thick_per_frame = min(2, v_per_line)  # 2 per frame for bay sides
        dist['thick']['count'] = v_frames * thick_per_frame
        
        remaining = (v_frames * v_per_line) - dist['thick']['count']
        
        if af_lines > 0 and col_counts['af_main'] > 0:
            af_ratio = min(af_lines / v_frames, 0.3)
            dist['af']['count'] = int(af_ratio * remaining)
            dist['main']['count'] = remaining - dist['af']['count']
        else:
            dist['main']['count'] = remaining

    def _distribute_v_supports_span_side(self, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
        """Distribute V Supports when thick_column = '3' (Both Span Side)"""
        # Thick columns on span side frames (front and back)
        total_bays = self.no_of_bays + 1
        span_side_frames = 2  # Front and back frames
        
        if v_frames <= span_side_frames:
            # All frames are span side
            dist['thick']['count'] = v_frames * v_per_line
        else:
            # Calculate how many V supports go to span side frames
            span_ratio = span_side_frames / total_bays
            thick_v_supports = int(span_ratio * v_frames * v_per_line)
            dist['thick']['count'] = thick_v_supports
            
            remaining = (v_frames * v_per_line) - thick_v_supports
            if af_lines > 0 and col_counts['af_main'] > 0:
                af_ratio = min(af_lines / v_frames, 0.3)
                dist['af']['count'] = int(af_ratio * remaining)
                dist['main']['count'] = remaining - dist['af']['count']
            else:
                dist['main']['count'] = remaining

    def _distribute_v_supports_all_4_side(self, dist, v_frames, v_per_line, cols_per_frame):
        """Distribute V Supports when thick_column = '4' (All 4 Side)"""
        # All columns are thick columns
        dist['thick']['count'] = v_frames * v_per_line
    
    # =============================================
    # HELPER METHODS
    # =============================================
    
    def _add_to_clamp_accumulator(self, accumulator, clamp_type, size, quantity):
        """Add clamps to accumulator (combines same type and size)"""
        if quantity <= 0:
            return
        key = (clamp_type, size)
        accumulator[key] = accumulator.get(key, 0) + quantity
    
    def _add_to_clamp_accumulator_separate(self, accumulator, component_name, size, quantity):
        """Add clamps without combining (for special components like purlin clamps)"""
        if quantity <= 0:
            return
        key = (component_name, size)
        accumulator[key] = accumulator.get(key, 0) + quantity
    
    def _create_clamp_components_from_accumulator(self, accumulator):
        """Create clamp component records from accumulator"""
        _logger.info("=== CREATING CLAMP COMPONENTS ===")
        
        for (clamp_identifier, size), quantity in accumulator.items():
            # Handle special component names with parentheses
            if '(' in clamp_identifier:
                base_clamp_type = clamp_identifier.split('(')[0].strip()
                component_name = clamp_identifier
            else:
                base_clamp_type = clamp_identifier
                component_name = f"{clamp_identifier} - {size}"
            
            # Search for matching master record
            master_record = self.env['accessories.master'].search([
                ('name', '=', base_clamp_type),
                ('category', '=', 'clamps'),
                ('size_specification', '=', size),
                ('active', '=', True)
            ], limit=1)
            
            vals = {
                'green_master_id': self.id,
                'section': 'clamps',
                'name': component_name,
                'nos': int(quantity),
                'size_specification': size,
                'unit_price': master_record.unit_price if master_record else 0.0,
                'is_calculated': True,
                'description': f"Auto-calculated {component_name}",
            }
            
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            self.env['accessories.component.line'].create(vals)
            _logger.info(f"  Created: {component_name} - Qty: {quantity}")
    
    # =============================================
    # DATA RETRIEVAL METHODS  
    # =============================================
    
    def _get_bottom_chord_data(self):
        """Get bottom chord data from truss components"""
        bottom_chord = self.truss_component_ids.filtered(
            lambda c: 'Bottom Chord' in c.name and 'Female' not in c.name and 
            'V Support' not in c.name
        )
        data = {'count': 0, 'size': None}
        if bottom_chord:
            data['count'] = sum(bottom_chord.mapped('nos'))
            for component in bottom_chord:
                if component.pipe_id and component.pipe_id.pipe_size:
                    data['size'] = f"{component.pipe_id.pipe_size.size_in_mm:.0f}mm"
                    break
        return data
    
    def _get_v_support_count(self):
        """Get V support count from truss components"""
        v_support = self.truss_component_ids.filtered(lambda c: c.name == 'V Support Bottom Chord')
        return v_support.nos if v_support else 0
    
    def _get_big_arch_data(self):
        """Get big arch data from truss components"""
        big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        data = {'count': 0, 'size': None}
        if big_arch:
            data['count'] = big_arch.nos
            if big_arch.pipe_id and big_arch.pipe_id.pipe_size:
                data['size'] = f"{big_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_small_arch_data(self):
        """Get small arch data from truss components"""
        small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        data = {'count': 0, 'size': None}
        if small_arch:
            data['count'] = small_arch.nos
            if small_arch.pipe_id and small_arch.pipe_id.pipe_size:
                data['size'] = f"{small_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_vent_big_support_count(self):
        """Get vent support count for big arch"""
        vent_support = self.truss_component_ids.filtered(
            lambda c: c.name == 'Vent Support for Big Arch')
        return vent_support.nos if vent_support else 0
    
    def _get_small_arch_support_count(self):
        """Get total small arch support count"""
        total = 0
        small_big = self.truss_component_ids.filtered(
            lambda c: c.name == 'Arch Support Small for Big Arch')
        small_small = self.truss_component_ids.filtered(
            lambda c: c.name == 'Arch Support Small for Small Arch')
        if small_big:
            total += small_big.nos
        if small_small:
            total += small_small.nos
        return total
    
    def _get_big_arch_support_count(self):
        """Get total big arch support count"""
        total = 0
        big_big = self.truss_component_ids.filtered(
            lambda c: c.name == 'Arch Support Big (Big Arch)')
        big_small = self.truss_component_ids.filtered(
            lambda c: c.name == 'Arch Support Big (Small Arch)')
        if big_big:
            total += big_big.nos
        if big_small:
            total += big_small.nos
        return total
    
    def _get_arch_support_straight_middle_data(self):
        """Get arch support straight middle data"""
        arch_support = self.truss_component_ids.filtered(
            lambda c: c.name == 'Arch Support Straight Middle')
        data = {'count': 0, 'size': None}
        if arch_support:
            data['count'] = arch_support.nos
            if arch_support.pipe_id and arch_support.pipe_id.pipe_size:
                data['size'] = f"{arch_support.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_middle_column_data(self):
        """Get middle column data from frame components"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Middle Columns')
        data = {'count': 0, 'size': None}
        if middle_columns:
            data['count'] = middle_columns.nos
            if middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
                data['size'] = f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_main_column_pipe_size(self):
        """Get Main Column pipe size"""
        main_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Main Columns')
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Fallback to AF Main Columns if Main Columns not found
        af_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'AF Main Columns')
        if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
            return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return None
    
    def _get_thick_column_pipe_size(self):
        """Get Thick Column pipe size"""
        thick_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Thick Columns')
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_af_column_pipe_size(self):
        """Get AF Column pipe size (Anchor Frame columns)"""
        af_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'AF Main Columns')
        if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
            return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_af_support_column_pipe_size(self):
        """Get pipe size for AF support columns (priority: AF Main → Thick → Main)
        NOTE: This is used for V Support calculations, NOT for middle columns in ASC
        """
        # First check for AF Main Columns
        af_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'AF Main Columns')
        if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
            return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Then check Thick Columns
        thick_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Thick Columns')
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Finally check Main Columns
        main_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Main Columns')
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return None
    
    def _get_middle_column_pipe_size(self):
        """Get Middle Column pipe size"""
        middle_columns = self.frame_component_ids.filtered(
            lambda c: c.name == 'Middle Columns')
        if middle_columns and middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
            return f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_asc_pipe_size(self):
        """Get ASC pipe size from ASC components"""
        if hasattr(self, 'asc_component_ids'):
            asc_pipes = self.asc_component_ids.filtered(
                lambda c: 'ASC Pipes' in c.name)
            if asc_pipes and asc_pipes[0].pipe_id and asc_pipes[0].pipe_id.pipe_size:
                return f"{asc_pipes[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_small_arch_purlin_size(self):
        """Get Small Arch Purlin pipe size from truss components"""
        small_arch_purlin = self.truss_component_ids.filtered(
            lambda c: 'Small Arch Purlin' in c.name or 'Small Purlin' in c.name)
        if small_arch_purlin and small_arch_purlin.pipe_id and small_arch_purlin.pipe_id.pipe_size:
            return f"{small_arch_purlin.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Fallback to Small Arch size if purlin not found
        small_arch_data = self._get_small_arch_data()
        return small_arch_data['size']

    # =============================================
    # UI METHODS
    # =============================================
    
    def get_clamp_calculation_details(self):
        """Get detailed clamp calculations for wizard display"""
        details = []
        sequence = 10
        
        # Process each clamp type and collect details
        temp_accumulator = {}
        arch_support_type = getattr(self, 'arch_support_type', 'none')
        
        # M or W Type Clamps
        if self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(
                    temp_accumulator, 'M TYPE CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        elif self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(
                    temp_accumulator, 'W TYPE CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # Arch Support Clamps
        if arch_support_type == 'arch_2_bottom':
            self._accumulate_arch_2_bottom_clamps(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(
                    temp_accumulator, 'ARCH TO BOTTOM CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        elif arch_support_type == 'arch_2_straight':
            self._accumulate_arch_2_straight_clamps(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(
                    temp_accumulator, 'ARCH TO STRAIGHT CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # Purlin Clamps
        self._accumulate_purlin_clamps(temp_accumulator)
        if temp_accumulator:
            details.extend(self._convert_accumulator_to_details(
                temp_accumulator, 'PURLIN CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # V Support Clamps
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord:
            self._accumulate_v_support_main_column_clamps(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(
                    temp_accumulator, 'V SUPPORT CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # Vent Support Small Arch Clamps
        self._accumulate_vent_support_small_arch_clamps(temp_accumulator)
        if temp_accumulator:
            details.extend(self._convert_accumulator_to_details(
                temp_accumulator, 'VENT SUPPORT CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Cross Bracing Clamps
        self._accumulate_cross_bracing_clamps(temp_accumulator)
        if temp_accumulator:
            details.extend(self._convert_accumulator_to_details(
                temp_accumulator, 'CROSS BRACING CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Border Purlin Clamps
        self._accumulate_border_purlin_clamps(temp_accumulator)
        if temp_accumulator:
            details.extend(self._convert_accumulator_to_details(
                temp_accumulator, 'BORDER PURLIN CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # ASC Clamps
        if hasattr(self, 'is_side_coridoors') and self.is_side_coridoors:
            self._accumulate_asc_clamps_complete(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(
                    temp_accumulator, 'ASC CLAMPS', sequence))
                temp_accumulator.clear()
        
        return details
    
    def _convert_accumulator_to_details(self, accumulator, category, start_sequence):
        """Convert accumulator data to detail format for wizard"""
        details = []
        seq = start_sequence
        for (clamp_identifier, size), quantity in accumulator.items():
            # Extract base clamp type from identifier
            if '(' in clamp_identifier:
                clamp_type = clamp_identifier.split('(')[0].strip()
            else:
                clamp_type = clamp_identifier
            
            details.append({
                'sequence': seq,
                'category': category,
                'component': clamp_identifier,
                'clamp_type': clamp_type,
                'size': size,
                'quantity': quantity,
                'formula': f"Calculated from {category.lower()}",
                'unit_price': self._get_clamp_price(clamp_type, size),
            })
            seq += 10
        return details
    
    def _get_clamp_price(self, clamp_type, size):
        """Get clamp price from master data"""
        master_record = self.env['accessories.master'].search([
            ('name', '=', clamp_type),
            ('category', '=', 'clamps'),
            ('size_specification', '=', size),
            ('active', '=', True)
        ], limit=1)
        return master_record.unit_price if master_record else 0.0
    
    # =============================================
    # ONCHANGE METHODS
    # =============================================
    
    @api.onchange('clamp_type')
    def _onchange_clamp_type(self):
        """Handle clamp type changes"""
        if self.clamp_type == 'none':
            self.big_purlin_clamp_type_first = False
            self.big_purlin_clamp_type_second = False
            self.small_purlin_clamp_type_first = False
            self.small_purlin_clamp_type_second = False
            self.bottom_chord_clamp_type = 'single'
        elif self.clamp_type == 'w_type':
            self.bottom_chord_clamp_type = 'single'
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
                self.small_purlin_clamp_type_second = 'half_clamp'
        elif self.clamp_type == 'm_type':
            if not self.bottom_chord_clamp_type:
                self.bottom_chord_clamp_type = 'single'
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
                self.small_purlin_clamp_type_second = 'half_clamp'
    
    @api.onchange('big_purlin_clamp_type_first')
    def _onchange_big_purlin_first(self):
        """Auto-set second type when first is selected"""
        if self.big_purlin_clamp_type_first and not self.big_purlin_clamp_type_second:
            self.big_purlin_clamp_type_second = 'half_clamp'
    
    @api.onchange('small_purlin_clamp_type_first')
    def _onchange_small_purlin_first(self):
        """Auto-set second type when first is selected"""
        if self.small_purlin_clamp_type_first and not self.small_purlin_clamp_type_second:
            self.small_purlin_clamp_type_second = 'half_clamp'
    
    # =============================================
    # ACTION METHODS
    # =============================================
    
    def action_view_clamp_details(self):
        """Open clamp calculation wizard to show detailed calculations"""
        self.ensure_one()
        
        # Create wizard record
        wizard = self.env['clamp.calculation.detail'].with_context(
            active_id=self.id).create({'green_master_id': self.id})
        
        # Calculate clamps to populate wizard
        wizard.calculate_clamps()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clamp Calculation Details',
            'res_model': 'clamp.calculation.detail',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'green2_accessories_clamps.view_clamp_calculation_detail_form').id,
            'target': 'new',
            'context': dict(self.env.context, active_id=self.id),
        }