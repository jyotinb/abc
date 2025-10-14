# green2_accessories_clamps/models/additional_clamps.py
# Additional clamp calculations including ASC Support Pipe Clamps

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AdditionalClamps(models.Model):
    """
    Mixin class for additional clamp calculations
    Inherits from green.master to add extra clamp logic
    """
    _inherit = 'green.master'
    
    # =============================================
    # ASC SUPPORT PIPE CLAMPS
    # =============================================
    
    def _accumulate_asc_support_pipe_clamps(self, accumulator):
        """
        Calculate ASC Support Pipe Clamps
        
        Part A: Full Clamps = TOTAL No of ASC Support Pipes across ALL sides × support_per_hockey
        Part B: Configuration-based clamps for each side × support_per_hockey
        """
        # Check if calculation should proceed
        if not self._should_calculate_asc_support_clamps():
            return
            
        _logger.info("=== ASC SUPPORT PIPE CLAMPS ===")
        
        # Get support_per_hockey multiplier
        support_per_hockey = int(getattr(self, 'support_per_hockey', 1))
        _logger.info(f"  Support per Hockey: {support_per_hockey}")
        
        # Part A: Total ASC Support Pipe Clamps (sum of all sides) × support_per_hockey
        total_asc_support_count = self._get_total_asc_support_pipe_count()
        if total_asc_support_count > 0:
            asc_pipe_size = self._get_asc_pipe_size()
            if asc_pipe_size:
                final_count = total_asc_support_count * support_per_hockey
                self._add_to_clamp_accumulator(
                    accumulator, 'Full Clamp', asc_pipe_size, final_count
                )
                _logger.info(f"  Part A - ASC Support Pipes: {total_asc_support_count} × {support_per_hockey} = {final_count} × Full Clamp - {asc_pipe_size}")
        
        # Create temporary accumulator for Part B to apply multiplier
        temp_accumulator = {}
        
        # Part B: Configuration-based clamps (calculated for each existing side)
        _logger.info("  Part B - Configuration-based clamps:")
        thick_column = getattr(self, 'thick_column', '0')
        no_anchor_frame_lines = int(getattr(self, 'no_anchor_frame_lines', 0))
        no_middle_columns_per_af = int(getattr(self, 'no_column_big_frame', 0))
        
        # Process each ASC side if it exists - collect in temp accumulator
        if getattr(self, 'front_span_asc', False):
            self._calculate_front_span_asc_support_clamps(
                temp_accumulator, thick_column, no_anchor_frame_lines, no_middle_columns_per_af
            )
        
        if getattr(self, 'back_span_asc', False):
            self._calculate_back_span_asc_support_clamps(
                temp_accumulator, thick_column, no_anchor_frame_lines, no_middle_columns_per_af
            )
        
        if getattr(self, 'front_bay_asc', False):
            self._calculate_front_bay_asc_support_clamps(
                temp_accumulator, thick_column, no_anchor_frame_lines
            )
        
        if getattr(self, 'back_bay_asc', False):
            self._calculate_back_bay_asc_support_clamps(
                temp_accumulator, thick_column, no_anchor_frame_lines
            )
        
        # Apply support_per_hockey multiplier to Part B and add to main accumulator
        for (clamp_type, size), quantity in temp_accumulator.items():
            final_quantity = quantity * support_per_hockey
            self._add_to_clamp_accumulator(accumulator, clamp_type, size, final_quantity)
            _logger.info(f"    {clamp_type} - {size}: {quantity} × {support_per_hockey} = {final_quantity}")
    
    def _calculate_front_span_asc_support_clamps(self, accumulator, thick_column, af_lines, middle_cols_per_af):
        """Calculate Front Span ASC Support clamps"""
        _logger.info("  Front Span ASC Support:")
        
        if thick_column in ['1', '2']:  # 4 Corner OR 2 Bay Side
            # Thick Column clamps
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
            
            # AF/Main Column logic
            if af_lines >= 1:
                # Middle Columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and middle_cols_per_af > 0:
                    qty = self.no_of_spans * middle_cols_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
                
                # AF Main Columns
                af_main_size = self._get_af_column_pipe_size()
                if af_main_size:
                    qty = self.no_of_spans - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                # Main Columns only
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_spans - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['3', '4']:  # 2 Span Side OR All 4 Side
            # Thick Column clamps
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                qty = self.no_of_spans + 1
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
            
            # Middle Columns if AF Lines exist
            if af_lines >= 1:
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and middle_cols_per_af > 0:
                    qty = self.no_of_spans * middle_cols_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
        
        else:  # thick_column == '0'
            if af_lines > 0:
                # Middle Columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and middle_cols_per_af > 0:
                    qty = self.no_of_spans * middle_cols_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
                
                # AF Main Columns
                af_main_size = self._get_af_column_pipe_size()
                if af_main_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                # Main Columns only
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
    
    def _calculate_back_span_asc_support_clamps(self, accumulator, thick_column, af_lines, middle_cols_per_af):
        """Calculate Back Span ASC Support clamps"""
        _logger.info("  Back Span ASC Support:")
        
        if thick_column in ['1', '2']:  # 4 Corner OR 2 Bay Side
            # Thick Column clamps
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
            
            # AF/Main Column logic - Note: Back Span uses AF Lines >= 2
            if af_lines >= 2:
                # Middle Columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and middle_cols_per_af > 0:
                    qty = self.no_of_spans * middle_cols_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
                
                # AF Main Columns
                af_main_size = self._get_af_column_pipe_size()
                if af_main_size:
                    qty = self.no_of_spans - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                # Main Columns only
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_spans - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['3', '4']:  # 2 Span Side OR All 4 Side
            # Thick Column clamps
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                qty = self.no_of_spans + 1
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
            
            # Middle Columns if AF Lines > 1 (different from Front Span)
            if af_lines > 1:
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and middle_cols_per_af > 0:
                    qty = self.no_of_spans * middle_cols_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
        
        else:  # thick_column == '0'
            if af_lines > 1:
                # Middle Columns
                middle_size = self._get_middle_column_pipe_size()
                if middle_size and middle_cols_per_af > 0:
                    qty = self.no_of_spans * middle_cols_per_af
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
                
                # AF Main Columns
                af_main_size = self._get_af_column_pipe_size()
                if af_main_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                # Main Columns only
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_spans + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
    
    def _calculate_front_bay_asc_support_clamps(self, accumulator, thick_column, af_lines):
        """Calculate Front Bay ASC Support clamps"""
        _logger.info("  Front Bay ASC Support:")
        
        if thick_column in ['1', '3']:  # 4 Corner OR 2 Span Side
            if af_lines < 3:
                # Thick Columns
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
                
                # Main Columns
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_bays - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
            
            else:  # af_lines >= 3
                # Thick Columns
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
                
                # AF Columns
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    qty_af = af_lines - 2
                    if qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                        _logger.info(f"    {qty_af} × Full Clamp - {af_size} (AF)")
                
                # Main Columns
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty_main = (self.no_of_bays + 1) - af_lines
                    if qty_main > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                        _logger.info(f"    {qty_main} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['2', '4']:  # 2 Bay Side OR All 4 Side
            # Thick Columns
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                qty = self.no_of_bays + 1
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
        
        else:  # thick_column == '0'
            if af_lines == 0:
                # Main Columns only
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_bays + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
            else:  # af_lines > 0
                # AF Columns
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_lines)
                    _logger.info(f"    {af_lines} × Full Clamp - {af_size} (AF)")
                
                # Main Columns
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = (self.no_of_bays + 1) - af_lines
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
    
    def _calculate_back_bay_asc_support_clamps(self, accumulator, thick_column, af_lines):
        """Calculate Back Bay ASC Support clamps"""
        _logger.info("  Back Bay ASC Support:")
        
        # Logic is identical to Front Bay
        if thick_column in ['1', '3']:  # 4 Corner OR 2 Span Side
            if af_lines < 3:
                # Thick Columns
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
                
                # Main Columns
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_bays - 1
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
            
            else:  # af_lines >= 3
                # Thick Columns
                thick_size = self._get_thick_column_pipe_size()
                if thick_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                    _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
                
                # AF Columns
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    qty_af = af_lines - 2
                    if qty_af > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                        _logger.info(f"    {qty_af} × Full Clamp - {af_size} (AF)")
                
                # Main Columns
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty_main = (self.no_of_bays + 1) - af_lines
                    if qty_main > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                        _logger.info(f"    {qty_main} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['2', '4']:  # 2 Bay Side OR All 4 Side
            # Thick Columns
            thick_size = self._get_thick_column_pipe_size()
            if thick_size:
                qty = self.no_of_bays + 1
                self._add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
        
        else:  # thick_column == '0'
            if af_lines == 0:
                # Main Columns only
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = self.no_of_bays + 1
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
            else:  # af_lines > 0
                # AF Columns
                af_size = self._get_af_column_pipe_size()
                if af_size:
                    self._add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_lines)
                    _logger.info(f"    {af_lines} × Full Clamp - {af_size} (AF)")
                
                # Main Columns
                main_size = self._get_main_column_pipe_size()
                if main_size:
                    qty = (self.no_of_bays + 1) - af_lines
                    if qty > 0:
                        self._add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
    
    # =============================================
    # HELPER METHODS
    # =============================================
    
    def _get_total_asc_support_pipe_count(self):
        """
        Get the TOTAL count of ASC Support Pipes across ALL sides
        This sums up ASC Support components from all four sides
        """
        total_count = 0
        
        if hasattr(self, 'asc_component_ids'):
            # Get all ASC Support Pipe components
            asc_support = self.asc_component_ids.filtered(
                lambda c: 'ASC Support' in c.name or 'ASC Support Pipe' in c.name
            )
            if asc_support:
                total_count = sum(asc_support.mapped('nos'))
        
        _logger.info(f"    Total ASC Support Pipe count from all sides: {total_count}")
        return total_count
    
    def _should_calculate_asc_support_clamps(self):
        """Check if ASC Support clamps should be calculated"""
        # Calculate if we have ASC Support components or any ASC sides active
        has_asc_support = self._get_total_asc_support_pipe_count() > 0
        has_asc_sides = (
            getattr(self, 'front_span_asc', False) or
            getattr(self, 'back_span_asc', False) or
            getattr(self, 'front_bay_asc', False) or
            getattr(self, 'back_bay_asc', False)
        )
        return has_asc_support or has_asc_sides
    
    # =============================================
    # VIEW DETAILS INTEGRATION
    # =============================================
    
    # def get_clamp_calculation_details(self):
        # """Override to include ASC Support clamps in details"""
        # # Get details from parent class (all existing clamps)
        # details = super().get_clamp_calculation_details()
        
        # # Add ASC Support clamps if they exist
        # if self._should_calculate_asc_support_clamps():
            # temp_accumulator = {}
            # self._accumulate_asc_support_pipe_clamps(temp_accumulator)
            
            # if temp_accumulator:
                # # Find the next sequence number
                # max_sequence = max([d['sequence'] for d in details], default=0)
                # next_sequence = max_sequence + 100
                
                # # Add ASC Support clamp details
                # details.extend(self._convert_accumulator_to_details(
                    # temp_accumulator, 'ASC SUPPORT PIPE CLAMPS', next_sequence))
        
        # return details