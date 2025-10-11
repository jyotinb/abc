# green2_accessories_clamps/models/green_master_clamps.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from math import ceil
import logging

_logger = logging.getLogger(__name__)

class GreenMasterClamps(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # ALL ORIGINAL FIELD DECLARATIONS
    # =============================================
    
    bay_side_border_purlin = fields.Integer(
        'Bay Side Border Purlin', 
        default=0,
        help="Number of bay side border purlins (defined here for compatibility)"
    )
    
    span_side_border_purlin = fields.Integer(
        'Span Side Border Purlin', 
        default=0,
        help="Number of span side border purlins (defined here for compatibility)"
    )
    
    # MODIFIED: Clamp type now computed from arch_support_type
    clamp_type = fields.Selection([
        ('w_type', 'W Type'),
        ('m_type', 'M Type'),
        ('none', 'None')
    ], string='Clamp Type', compute='_compute_clamp_type', store=True, readonly=True,
       help="Automatically set based on Arch Support Type selection in Truss Configuration")
    
    # Add this field definition
    arch_support_type = fields.Selection([
        ('none', 'None'),
        ('w', 'W Type'),
        ('m', 'M Type'),
        ('arch_2_bottom', 'Arch to Bottom'),
        ('arch_2_straight', 'Arch to Straight Middle')
    ], string='Arch Support Type', default='none', tracking=True)
    
    # Purlin clamp configurations - Now applies to both W and M Type
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
    
    # Bottom chord clamp type for M Type
    bottom_chord_clamp_type = fields.Selection([
        ('single', 'Single'),
        ('triple', 'Triple')
    ], string='Bottom Chord Clamp Type', default='single', tracking=True)
    
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
    
    # Override base field to add size override capability
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
                # If arch_support_type field doesn't exist (truss module not installed)
                record.clamp_type = 'none'
    
    # =============================================
    # VALIDATION
    # =============================================
    @api.constrains('big_purlin_clamp_type_first', 'big_purlin_clamp_type_second',
                    'small_purlin_clamp_type_first', 'small_purlin_clamp_type_second')
    def _check_purlin_clamp_configuration(self):
        """Validate that if first type is selected, second type cannot be blank"""
        for record in self:
            if record.big_purlin_clamp_type_first and not record.big_purlin_clamp_type_second:
                raise ValidationError("Big Purlin Second Type cannot be blank when First Type is selected!")
            
            if record.small_purlin_clamp_type_first and not record.small_purlin_clamp_type_second:
                raise ValidationError("Small Purlin Second Type cannot be blank when First Type is selected!")
    
    @api.depends('clamps_component_ids', 'clamps_component_ids.size_specification', 'clamps_component_ids.nos')
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
                 'thick_column_position', 'no_anchor_frame_lines')
    def _compute_border_purlin_clamps_summary(self):
        """Compute border purlin clamps summary"""
        for record in self:
            if int(record.bay_side_border_purlin or 0) == 0 and \
               int(record.span_side_border_purlin or 0) == 0:
                record.border_purlin_clamps_summary = ""
                continue
            
            summary_parts = []
            
            # Bay Side
            if int(record.bay_side_border_purlin or 0) > 0:
                bay_info = f"Bay Side: {record.bay_side_border_purlin}"
                if hasattr(record, 'front_bay_asc') and record.front_bay_asc:
                    bay_info += " (Front ASC)"
                if hasattr(record, 'back_bay_asc') and record.back_bay_asc:
                    bay_info += " (Back ASC)"
                summary_parts.append(bay_info)
            
            # Span Side
            if int(record.span_side_border_purlin or 0) > 0:
                span_info = f"Span Side: {record.span_side_border_purlin}"
                if hasattr(record, 'front_span_asc') and record.front_span_asc:
                    span_info += " (Front ASC)"
                if hasattr(record, 'back_span_asc') and record.back_span_asc:
                    span_info += " (Back ASC)"
                summary_parts.append(span_info)
            
            # Thick Column Position
            if hasattr(record, 'thick_column_position') and record.thick_column_position != 'none':
                thick_label = dict(record._fields['thick_column_position'].selection).get(record.thick_column_position, '')
                summary_parts.append(f"Thick: {thick_label}")
            
            # Anchor Frames
            if hasattr(record, 'no_anchor_frame_lines') and record.no_anchor_frame_lines > 0:
                summary_parts.append(f"AF Lines: {record.no_anchor_frame_lines}")
            
            record.border_purlin_clamps_summary = " | ".join(summary_parts) if summary_parts else "No border purlins"
    
    def _calculate_all_accessories(self):
        """Extend to add clamp calculations"""
        super()._calculate_all_accessories()
        self._calculate_clamp_components()
    
    def _calculate_clamp_components(self):
        """Calculate all clamp components"""
        # Clear existing clamp components
        self.clamps_component_ids.unlink()
        
        # Calculate advanced clamps
        self._calculate_advanced_clamps()
    
    def _calculate_advanced_clamps(self):
        """Main method for advanced clamp calculations"""
        # Check if any clamps are needed
        arch_support_type = getattr(self, 'arch_support_type', 'none')
        
        if (self.clamp_type == 'none' and 
            arch_support_type in ['none', ''] and
            int(self.bay_side_border_purlin or 0) <= 0 and 
            int(self.span_side_border_purlin or 0) <= 0 and
            not (hasattr(self, 'is_bottom_chord') and self.is_bottom_chord and int(self.v_support_bottom_chord_frame or 0) > 0)):
            _logger.info("No clamps configuration detected, skipping clamp calculations")
            return
        
        # Use accumulator pattern to group clamps by type and size
        clamp_accumulator = {}
        
        # W Type or M Type clamps
        if self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(clamp_accumulator)
        elif self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(clamp_accumulator)
        
        # NEW: Arch to Bottom Support clamps
        if arch_support_type == 'arch_2_bottom':
            self._accumulate_arch_2_bottom_clamps(clamp_accumulator)
        
        # NEW: Arch to Straight Middle clamps  
        elif arch_support_type == 'arch_2_straight':
            self._accumulate_arch_2_straight_clamps(clamp_accumulator)
        
        # Purlin clamps - Now calculated for both W and M types if configured
        if self.clamp_type in ['w_type', 'm_type']:
            self._accumulate_purlin_clamps(clamp_accumulator)
        
        # V Support to Main Column clamps
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord and int(self.v_support_bottom_chord_frame or 0) > 0:
            self._accumulate_v_support_main_column_clamps(clamp_accumulator)
        
        # Border Purlin clamps
        self._accumulate_border_purlin_clamps(clamp_accumulator)
        
        # Arch Middle Purlin clamps
        self._accumulate_arch_middle_purlin_clamps(clamp_accumulator)
        
        # Create clamp components from accumulator
        self._create_clamp_components_from_accumulator(clamp_accumulator)
    
    def _accumulate_arch_2_bottom_clamps(self, accumulator):
        """NEW METHOD: Accumulate clamps for Arch to Bottom Support configuration"""
        # Get component data
        bottom_chord_data = self._get_bottom_chord_data()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        
        # Get the count of Small Arch Support components (since only Small are calculated)
        small_arch_support_count = self._get_small_arch_support_count()
        
        if small_arch_support_count > 0:
            # Full clamps = No of Arch to Bottom support, size: Bottom Pipe size
            if bottom_chord_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], small_arch_support_count)
            
            # Full clamps = No of Arch to Bottom support /2, size: Big Arch Pipe size
            if big_arch_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], small_arch_support_count // 2)
            
            # Full clamps = No of Arch to Bottom support /2, size: Small Arch Pipe size
            if small_arch_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_support_count // 2)
        
        # Also add clamps for Arch Support Straight Middle if it exists
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        if arch_support_straight_middle_data['count'] > 0:
            if bottom_chord_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], 
                                              arch_support_straight_middle_data['count'])
            if big_arch_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], 
                                              arch_support_straight_middle_data['count'])
    
    def _accumulate_arch_2_straight_clamps(self, accumulator):
        """NEW METHOD: Accumulate clamps for Arch to Straight Middle configuration"""
        # Get component data
        bottom_chord_data = self._get_bottom_chord_data()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        
        # Get the count of Big Arch Support components (since only Big are calculated)
        big_arch_support_count = self._get_big_arch_support_count()
        
        if big_arch_support_count > 0:
            # Full clamps = No of Arch to Bottom support, size: Bottom Pipe size
            if bottom_chord_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], big_arch_support_count)
            
            # Full clamps = No of Arch to Bottom support /2, size: Big Arch Pipe size
            if big_arch_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], big_arch_support_count // 2)
            
            # Full clamps = No of Arch to Bottom support /2, size: Small Arch Pipe size
            if small_arch_data['size']:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], big_arch_support_count // 2)
        
        # Also add clamps for Arch Support Straight Middle if it exists
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        if arch_support_straight_middle_data['count'] > 0 and big_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], 
                                          arch_support_straight_middle_data['count'])
    
    def _get_small_arch_support_count(self):
        """Get total count of Small Arch Support components"""
        total_count = 0
        small_big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Arch Support Small for Big Arch')
        small_small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Arch Support Small for Small Arch')
        
        if small_big_arch:
            total_count += small_big_arch.nos
        if small_small_arch:
            total_count += small_small_arch.nos
        
        return total_count
    
    def _get_big_arch_support_count(self):
        """Get total count of Big Arch Support components"""
        total_count = 0
        big_big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Arch Support Big (Big Arch)')
        big_small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Arch Support Big (Small Arch)')
        
        if big_big_arch:
            total_count += big_big_arch.nos
        if big_small_arch:
            total_count += big_small_arch.nos
        
        return total_count
    
    def _accumulate_w_type_clamps(self, accumulator):
        """Accumulate W Type clamps - UPDATED WITH NEW LOGIC"""
        # Get component data
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_big_support_count = self._get_vent_big_support_count()
        arch_support_straight_middle_data = self._get_arch_support_straight_middle_data()
        middle_column_data = self._get_middle_column_data()
        
        # Bottom Chord clamps
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            qty = (bottom_chord_data['count'] * 3) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # Big Arch clamps - MODIFIED to include Vent Support
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_big_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # Small Arch clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        
        # NEW: Arch Support Straight Middle clamps - Both Full and Half
        if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
            # Full Clamps
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', arch_support_straight_middle_data['size'], 
                                          arch_support_straight_middle_data['count'])
            # Half Clamps
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', arch_support_straight_middle_data['size'], 
                                          arch_support_straight_middle_data['count'])
        
        # NEW: Middle Column clamps - Both Full and Half
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            # Full Clamps
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
            # Half Clamps
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
    
    def _accumulate_m_type_clamps(self, accumulator):
        """Accumulate M Type clamps - UPDATED WITH NEW LOGIC"""
        # Get component data
        bottom_chord_data = self._get_bottom_chord_data()
        v_support_count = self._get_v_support_count()
        big_arch_data = self._get_big_arch_data()
        small_arch_data = self._get_small_arch_data()
        vent_big_support_count = self._get_vent_big_support_count()
        middle_column_data = self._get_middle_column_data()
        
        # Bottom Chord clamps
        if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
            if self.bottom_chord_clamp_type == 'single':
                qty = (bottom_chord_data['count'] * 3) + v_support_count
            else:  # triple
                qty = (bottom_chord_data['count'] * 5) + v_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        
        # Big Arch clamps - MODIFIED to include Vent Support
        if big_arch_data['count'] > 0 and big_arch_data['size']:
            qty = (big_arch_data['count'] * 2) + vent_big_support_count
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        
        # Small Arch clamps
        if small_arch_data['count'] > 0 and small_arch_data['size']:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_data['count'])
        
        # NEW: Middle Column clamps - Both Full and Half
        if middle_column_data['count'] > 0 and middle_column_data['size']:
            # Full Clamps
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
            # Half Clamps
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_column_data['size'], 
                                          middle_column_data['count'])
    
    def _accumulate_purlin_clamps(self, accumulator):
        """NEW METHOD: Accumulate purlin clamps for both W and M types"""
        # Get Arch Middle Purlin data (NOT Big/Small Arch data)
        arch_middle_big_data = self._get_arch_middle_purlin_big_data()
        arch_middle_small_data = self._get_arch_middle_purlin_small_data()
        
        # Big Purlin clamps (= Arch Middle Purlin Big Arch)
        if arch_middle_big_data['count'] > 0 and arch_middle_big_data['size'] and self.big_purlin_clamp_type_first:
            # First Type
            qty_first = self.no_of_spans * 2
            clamp_name = 'Full Clamp' if self.big_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            self._add_to_clamp_accumulator(accumulator, clamp_name, arch_middle_big_data['size'], qty_first)
            
            # Second Type (must exist if first type exists due to validation)
            if self.big_purlin_clamp_type_second:
                qty_second = arch_middle_big_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if self.big_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    self._add_to_clamp_accumulator(accumulator, clamp_name, arch_middle_big_data['size'], qty_second)
        
        # Small Purlin clamps (= Arch Middle Purlin Small Arch)
        if arch_middle_small_data['count'] > 0 and arch_middle_small_data['size'] and self.small_purlin_clamp_type_first:
            # First Type
            qty_first = self.no_of_spans * 2
            clamp_name = 'Full Clamp' if self.small_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            self._add_to_clamp_accumulator(accumulator, clamp_name, arch_middle_small_data['size'], qty_first)
            
            # Second Type (must exist if first type exists due to validation)
            if self.small_purlin_clamp_type_second:
                qty_second = arch_middle_small_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = 'Half Clamp' if self.small_purlin_clamp_type_second == 'half_clamp' else 'T Joint'
                    self._add_to_clamp_accumulator(accumulator, clamp_name, arch_middle_small_data['size'], qty_second)
    
    def _accumulate_v_support_main_column_clamps(self, accumulator):
        """Accumulate V Support to Main Column clamps - MODIFIED for Column Size"""
        v_support_count = self._get_v_support_count()
        if v_support_count > 0:
            # Get column size instead of V support pipe size
            column_size = self._get_column_pipe_size()
            if column_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', column_size, v_support_count)
    
    def _accumulate_border_purlin_clamps(self, accumulator):
        """
        Accumulate border purlin clamps with full specification support
        Handles:
        - Half Clamps and Full Clamps separately
        - Front/Back sides separately
        - ASC presence per side
        - Thick Column positions
        - Anchor Frame Lines
        """
        # BAY SIDE BORDER PURLIN
        if int(self.bay_side_border_purlin or 0) > 0:
            self._calculate_bay_side_border_clamps(accumulator)
        
        # SPAN SIDE BORDER PURLIN
        if int(self.span_side_border_purlin or 0) > 0:
            self._calculate_span_side_border_clamps(accumulator)
        
        # ANCHOR FRAME LINES (only for span side)
        if int(getattr(self, 'no_anchor_frame_lines', 0)) > 0 and int(self.span_side_border_purlin or 0) > 0:
            self._calculate_anchor_frame_border_clamps(accumulator)

    def _calculate_bay_side_border_clamps(self, accumulator):
        """Calculate Bay Side Border Purlin clamps"""
        bay_side_border_purlin = int(self.bay_side_border_purlin)
        
        # FRONT BAY
        if hasattr(self, 'front_bay_asc') and self.front_bay_asc:
            self._add_bay_side_clamps_with_asc(accumulator, 'front')
        else:
            self._add_bay_side_clamps_without_asc(accumulator, 'front')
        
        # BACK BAY
        if hasattr(self, 'back_bay_asc') and self.back_bay_asc:
            self._add_bay_side_clamps_with_asc(accumulator, 'back')
        else:
            self._add_bay_side_clamps_without_asc(accumulator, 'back')

    def _add_bay_side_clamps_with_asc(self, accumulator, side):
        """Add bay side clamps when ASC exists"""
        bay_side_border_purlin = int(self.bay_side_border_purlin)
        asc_size = self._get_asc_pipe_size()
        
        if not asc_size:
            _logger.warning(f"{side.title()} Bay ASC is enabled but ASC pipe size not found")
            return
        
        # Half Clamps
        half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
        
        # Full Clamps
        full_qty = 2 * bay_side_border_purlin
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)

    def _add_bay_side_clamps_without_asc(self, accumulator, side):
        """Add bay side clamps when no ASC (based on thick column configuration)"""
        bay_side_border_purlin = int(self.bay_side_border_purlin)
        thick_column_position = getattr(self, 'thick_column_position', 'none')
        
        if thick_column_position == '4_corner':
            # Half Clamps: Main Column size
            main_column_size = self._get_main_column_pipe_size()
            if main_column_size:
                half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, half_qty)
            
            # Full Clamps: Thick Column size
            thick_column_size = self._get_thick_column_pipe_size()
            if thick_column_size:
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, full_qty)
        
        elif thick_column_position in ['2_bay_side', 'all_4_side']:
            # Both Half and Full: Thick Column size
            thick_column_size = self._get_thick_column_pipe_size()
            if thick_column_size:
                # Half Clamps
                half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_column_size, half_qty)
                
                # Full Clamps
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, full_qty)
        
        else:  # 'none' or '2_span_side'
            # Both Half and Full: Main Column size
            main_column_size = self._get_main_column_pipe_size()
            if main_column_size:
                # Half Clamps
                half_qty = (self.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, half_qty)
                
                # Full Clamps
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, full_qty)

    def _calculate_span_side_border_clamps(self, accumulator):
        """Calculate Span Side Border Purlin clamps"""
        span_side_border_purlin = int(self.span_side_border_purlin)
        
        # FRONT SPAN
        if hasattr(self, 'front_span_asc') and self.front_span_asc:
            self._add_span_side_clamps_with_asc(accumulator, 'front')
        else:
            self._add_span_side_clamps_without_asc(accumulator, 'front')
        
        # BACK SPAN
        if hasattr(self, 'back_span_asc') and self.back_span_asc:
            self._add_span_side_clamps_with_asc(accumulator, 'back')
        else:
            self._add_span_side_clamps_without_asc(accumulator, 'back')

    def _add_span_side_clamps_with_asc(self, accumulator, side):
        """Add span side clamps when ASC exists"""
        span_side_border_purlin = int(self.span_side_border_purlin)
        asc_size = self._get_asc_pipe_size()
        
        if not asc_size:
            _logger.warning(f"{side.title()} Span ASC is enabled but ASC pipe size not found")
            return
        
        # Half Clamps
        half_qty = (self.no_of_spans - 1) * span_side_border_purlin
        if half_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
        
        # Full Clamps
        full_qty = 2 * span_side_border_purlin
        if full_qty > 0:
            self._add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)

    def _add_span_side_clamps_without_asc(self, accumulator, side):
        """Add span side clamps when no ASC (based on thick column configuration)"""
        span_side_border_purlin = int(self.span_side_border_purlin)
        thick_column_position = getattr(self, 'thick_column_position', 'none')
        
        if thick_column_position == '4_corner':
            # Half Clamps: Main Column size
            main_column_size = self._get_main_column_pipe_size()
            if main_column_size:
                half_qty = (self.no_of_spans - 1) * span_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, half_qty)
            
            # Full Clamps: Thick Column size
            thick_column_size = self._get_thick_column_pipe_size()
            if thick_column_size:
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, full_qty)
        
        elif thick_column_position in ['2_span_side', 'all_4_side']:
            # Both Half and Full: Thick Column size
            thick_column_size = self._get_thick_column_pipe_size()
            if thick_column_size:
                # Half Clamps
                half_qty = (self.no_of_spans - 1) * span_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_column_size, half_qty)
                
                # Full Clamps
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_column_size, full_qty)
        
        else:  # 'none' or '2_bay_side'
            # Both Half and Full: Main Column size
            main_column_size = self._get_main_column_pipe_size()
            if main_column_size:
                # Half Clamps
                half_qty = (self.no_of_spans - 1) * span_side_border_purlin
                if half_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', main_column_size, half_qty)
                
                # Full Clamps
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_column_size, full_qty)

    def _calculate_anchor_frame_border_clamps(self, accumulator):
        """
        Calculate Anchor Frame border clamps (span side only)
        Special handling for anchor frame lines
        """
        no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        span_side_border_purlin = int(self.span_side_border_purlin)
        
        if no_anchor_frame_lines == 0:
            return
        
        if no_anchor_frame_lines == 1:
            # Show message to user (in actual implementation, use proper notification)
            _logger.info("ANCHOR FRAME NOTICE: We consider Anchor Frame Lines and ASC (if there) are at same line")
            
            # Determine size based on ASC presence
            if (hasattr(self, 'front_span_asc') and self.front_span_asc) or \
               (hasattr(self, 'back_span_asc') and self.back_span_asc):
                size = self._get_asc_pipe_size()
            else:
                size = self._get_big_column_pipe_size()
            
            if size:
                # Half Clamps only for anchor frame line = 1
                qty = self.no_of_spans * span_side_border_purlin
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', size, qty)
        
        elif no_anchor_frame_lines >= 2:
            # Front Span
            if hasattr(self, 'front_span_asc') and self.front_span_asc:
                size = self._get_asc_pipe_size()
            else:
                size = self._get_big_column_pipe_size()
            
            if size:
                qty = self.no_of_spans * span_side_border_purlin
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', size, qty)
            
            # Back Span
            if hasattr(self, 'back_span_asc') and self.back_span_asc:
                size = self._get_asc_pipe_size()
            else:
                size = self._get_big_column_pipe_size()
            
            if size:
                qty = self.no_of_spans * span_side_border_purlin
                if qty > 0:
                    self._add_to_clamp_accumulator(accumulator, 'Half Clamp', size, qty)
    
    def _accumulate_arch_middle_purlin_clamps(self, accumulator):
        """Accumulate arch middle purlin clamps - NOW HANDLED IN PURLIN CLAMPS METHOD"""
        # This is now handled by _accumulate_purlin_clamps() method
        # Keeping this method empty for backward compatibility
        pass
    
    def _add_to_clamp_accumulator(self, accumulator, clamp_type, size, quantity):
        """Add clamps to accumulator"""
        if quantity <= 0:
            return
        
        key = (clamp_type, size)
        if key in accumulator:
            accumulator[key] += quantity
        else:
            accumulator[key] = quantity
    
    def _create_clamp_components_from_accumulator(self, accumulator):
        """Create clamp components from accumulator"""
        for (clamp_type, size), quantity in accumulator.items():
            # Find matching master record
            master_record = self.env['accessories.master'].search([
                ('name', '=', clamp_type),
                ('category', '=', 'clamps'),
                ('size_specification', '=', size),
                ('active', '=', True)
            ], limit=1)
            
            unit_price = master_record.unit_price if master_record else 0.0
            
            component_name = f"{clamp_type} - {size}"
            
            vals = {
                'green_master_id': self.id,
                'section': 'clamps',
                'name': component_name,
                'nos': int(quantity),
                'size_specification': size,
                'unit_price': unit_price,
                'is_calculated': True,
                'description': f"Auto-calculated {clamp_type} for {size} pipes",
            }
            
            if master_record:
                vals['accessories_master_id'] = master_record.id
            
            self.env['accessories.component.line'].create(vals)
            _logger.info(f"Created clamp component: {component_name} - Qty: {quantity}")
    
    # =============================================
    # HELPER METHODS TO GET COMPONENT DATA
    # =============================================
    
    def _get_bottom_chord_data(self):
        """Get bottom chord component data"""
        bottom_chord = self.truss_component_ids.filtered(
            lambda c: 'Bottom Chord' in c.name and 'Female' not in c.name and 'V Support' not in c.name
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
        """Get V support count"""
        v_support = self.truss_component_ids.filtered(lambda c: c.name == 'V Support Bottom Chord')
        return v_support.nos if v_support else 0
    
    def _get_big_arch_data(self):
        """Get big arch data"""
        big_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
        data = {'count': 0, 'size': None}
        if big_arch:
            data['count'] = big_arch.nos
            if big_arch.pipe_id and big_arch.pipe_id.pipe_size:
                data['size'] = f"{big_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_small_arch_data(self):
        """Get small arch data"""
        small_arch = self.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
        data = {'count': 0, 'size': None}
        if small_arch:
            data['count'] = small_arch.nos
            if small_arch.pipe_id and small_arch.pipe_id.pipe_size:
                data['size'] = f"{small_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_vent_big_support_count(self):
        """Get vent support for big arch count"""
        vent_support = self.truss_component_ids.filtered(lambda c: c.name == 'Vent Support for Big Arch')
        return vent_support.nos if vent_support else 0
    
    def _get_arch_support_straight_middle_data(self):
        """Get arch support straight middle data"""
        arch_support = self.truss_component_ids.filtered(lambda c: c.name == 'Arch Support Straight Middle')
        data = {'count': 0, 'size': None}
        if arch_support:
            data['count'] = arch_support.nos
            if arch_support.pipe_id and arch_support.pipe_id.pipe_size:
                data['size'] = f"{arch_support.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_middle_column_data(self):
        """Get middle column data"""
        middle_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Middle Columns')
        data = {'count': 0, 'size': None}
        if middle_columns:
            data['count'] = middle_columns.nos
            if middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
                data['size'] = f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_arch_middle_purlin_big_data(self):
        """Get arch middle purlin big arch data"""
        arch_middle_big = self.lower_component_ids.filtered(lambda c: c.name == 'Arch Middle Purlin Big Arch')
        data = {'count': 0, 'size': None}
        if arch_middle_big:
            data['count'] = arch_middle_big.nos
            if arch_middle_big.pipe_id and arch_middle_big.pipe_id.pipe_size:
                data['size'] = f"{arch_middle_big.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_arch_middle_purlin_small_data(self):
        """Get arch middle purlin small arch data"""
        arch_middle_small = self.lower_component_ids.filtered(lambda c: c.name == 'Arch Middle Purlin Small Arch')
        data = {'count': 0, 'size': None}
        if arch_middle_small:
            data['count'] = arch_middle_small.nos
            if arch_middle_small.pipe_id and arch_middle_small.pipe_id.pipe_size:
                data['size'] = f"{arch_middle_small.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return data
    
    def _get_column_pipe_size(self):
        """Get column pipe size with priority: Thick Column → AF Column → Main Column"""
        # Priority 1: Thick Columns
        thick_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Thick Columns')
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Priority 2: AF Main Columns
        af_columns = self.frame_component_ids.filtered(lambda c: c.name == 'AF Main Columns')
        if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
            return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Priority 3: Main Columns
        main_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Main Columns')
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return None
    
    def _get_main_column_pipe_size(self):
        """Get Main Column pipe size (non-thick column)"""
        # Priority 1: Main Columns
        main_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Main Columns')
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Priority 2: If no Main Columns, use AF Main Columns (for structures with all anchor frames)
        af_columns = self.frame_component_ids.filtered(lambda c: c.name == 'AF Main Columns')
        if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
            return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
  
    
    def _get_thick_column_pipe_size(self):
        """Get Thick Column pipe size"""
        thick_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Thick Columns')
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    def _get_big_column_pipe_size(self):
        """
        Get Big Column pipe size (for anchor frames)
        Priority: AF Main Columns → Thick Columns → Main Columns
        """
        # Priority 1: AF Main Columns
        af_columns = self.frame_component_ids.filtered(lambda c: c.name == 'AF Main Columns')
        if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
            return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Priority 2: Thick Columns
        thick_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Thick Columns')
        if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
            return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        # Priority 3: Main Columns
        main_columns = self.frame_component_ids.filtered(lambda c: c.name == 'Main Columns')
        if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
            return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
        
        return None
    
    def _get_asc_pipe_size(self):
        """Get ASC pipe size"""
        if hasattr(self, 'asc_component_ids'):
            asc_pipes = self.asc_component_ids.filtered(lambda c: 'ASC Pipes' in c.name)
            if asc_pipes and asc_pipes[0].pipe_id and asc_pipes[0].pipe_id.pipe_size:
                return f"{asc_pipes[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
        return None
    
    # =============================================
    # WIZARD AND UI METHODS
    # =============================================
    
    def get_clamp_calculation_details(self):
        """Get detailed clamp calculations for display - UPDATED FOR NEW LOGIC"""
        details = []
        sequence = 10
        
        # Create temporary accumulator to get exact same calculations
        temp_accumulator = {}
        arch_support_type = getattr(self, 'arch_support_type', 'none')
        
        # M Type or W Type clamps
        if self.clamp_type == 'm_type':
            self._accumulate_m_type_clamps(temp_accumulator)
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'M TYPE CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        elif self.clamp_type == 'w_type':
            self._accumulate_w_type_clamps(temp_accumulator)
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'W TYPE CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Arch to Bottom Support clamps
        if arch_support_type == 'arch_2_bottom':
            self._accumulate_arch_2_bottom_clamps(temp_accumulator)
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'ARCH TO BOTTOM SUPPORT CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Arch to Straight Middle clamps
        elif arch_support_type == 'arch_2_straight':
            self._accumulate_arch_2_straight_clamps(temp_accumulator)
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'ARCH TO STRAIGHT MIDDLE CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Purlin clamps (for both W and M)
        if self.clamp_type in ['w_type', 'm_type']:
            self._accumulate_purlin_clamps(temp_accumulator)
            if temp_accumulator:
                details.extend(self._convert_accumulator_to_details(temp_accumulator, 'PURLIN CLAMPS', sequence))
                temp_accumulator.clear()
                sequence += 100
        
        # V Support
        if hasattr(self, 'is_bottom_chord') and self.is_bottom_chord and int(self.v_support_bottom_chord_frame or 0) > 0:
            self._accumulate_v_support_main_column_clamps(temp_accumulator)
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'V SUPPORT CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Border Purlin
        self._accumulate_border_purlin_clamps(temp_accumulator)
        if temp_accumulator:
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'BORDER PURLIN CLAMPS', sequence))
            temp_accumulator.clear()
            sequence += 100
        
        # Arch Middle Purlin
        self._accumulate_arch_middle_purlin_clamps(temp_accumulator)
        if temp_accumulator:
            details.extend(self._convert_accumulator_to_details(temp_accumulator, 'ARCH MIDDLE PURLIN CLAMPS', sequence))
            temp_accumulator.clear()
        
        return details
    
    def _convert_accumulator_to_details(self, accumulator, category, start_sequence):
        """Convert accumulator data to detail format for wizard"""
        details = []
        seq = start_sequence
        for (clamp_type, size), quantity in accumulator.items():
            details.append({
                'sequence': seq,
                'category': category,
                'component': f"{clamp_type} - {size}",
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
        """Handle clamp type change - Now this is computed, so handle related fields only"""
        if self.clamp_type == 'none':
            # Clear purlin clamp configurations
            self.big_purlin_clamp_type_first = False
            self.big_purlin_clamp_type_second = False
            self.small_purlin_clamp_type_first = False
            self.small_purlin_clamp_type_second = False
            self.bottom_chord_clamp_type = 'single'
        elif self.clamp_type == 'w_type':
            self.bottom_chord_clamp_type = 'single'
            # Set defaults if not already set
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
                self.small_purlin_clamp_type_second = 'half_clamp'
        elif self.clamp_type == 'm_type':
            if not self.bottom_chord_clamp_type:
                self.bottom_chord_clamp_type = 'single'
            # Set defaults if not already set
            if not self.big_purlin_clamp_type_first:
                self.big_purlin_clamp_type_first = 'full_clamp'
                self.big_purlin_clamp_type_second = 'half_clamp'
            if not self.small_purlin_clamp_type_first:
                self.small_purlin_clamp_type_first = 'full_clamp'
                self.small_purlin_clamp_type_second = 'half_clamp'
    
    @api.onchange('big_purlin_clamp_type_first')
    def _onchange_big_purlin_first(self):
        """Auto-set second type if first type is selected"""
        if self.big_purlin_clamp_type_first and not self.big_purlin_clamp_type_second:
            self.big_purlin_clamp_type_second = 'half_clamp'
    
    @api.onchange('small_purlin_clamp_type_first')
    def _onchange_small_purlin_first(self):
        """Auto-set second type if first type is selected"""
        if self.small_purlin_clamp_type_first and not self.small_purlin_clamp_type_second:
            self.small_purlin_clamp_type_second = 'half_clamp'
    
    def action_view_clamp_details(self):
        """Open clamp calculation details wizard"""
        # Ensure we have an ID (save if needed)
        self.ensure_one()
        
        # Create wizard with proper context
        wizard = self.env['clamp.calculation.detail'].with_context(active_id=self.id).create({
            'green_master_id': self.id,
        })
        
        # Calculate clamps immediately
        wizard.calculate_clamps()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clamp Calculation Details',
            'res_model': 'clamp.calculation.detail',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref('green2_accessories_clamps.view_clamp_calculation_detail_form').id,
            'target': 'new',
            'context': dict(self.env.context, active_id=self.id),
        }