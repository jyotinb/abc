# green2_accessories_clamps/models/clamp_types/asc_support_pipe_clamps.py
"""
ASC Support Pipe Clamp Calculations
Part A: Total ASC Support Pipe clamps (sum of all sides)
Part B: Configuration-based clamps for each side
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_asc_support_pipe_clamps(record, accumulator):
    """
    Calculate ASC Support Pipe Clamps
    
    Part A: Full Clamps = TOTAL No of ASC Support Pipes across ALL sides × support_per_hockey
    Part B: Configuration-based clamps for each side × support_per_hockey
    """
    # Check if calculation should proceed
    if not _should_calculate_asc_support_clamps(record):
        return
        
    _logger.info("=== ASC SUPPORT PIPE CLAMPS ===")
    
    # Get support_per_hockey multiplier
    support_per_hockey = int(getattr(record, 'support_hockeys', 1))
    if support_per_hockey <= 0:
        support_per_hockey = 1
    _logger.info(f"  Support per Hockey: {support_per_hockey}")
    
    # Part A: Total ASC Support Pipe Clamps (sum of all sides) × support_per_hockey
    total_asc_support_count = _get_total_asc_support_pipe_count(record)
    if total_asc_support_count > 0:
        asc_pipe_size = helpers.get_asc_pipe_size(record)
        if asc_pipe_size:
            final_count = total_asc_support_count  # Already multiplied in component calculation
            helpers.add_to_clamp_accumulator(
                accumulator, 'Full Clamp', asc_pipe_size, final_count
            )
            _logger.info(f"  Part A - ASC Support Pipes: {total_asc_support_count} × Full Clamp - {asc_pipe_size}")
    
    # Create temporary accumulator for Part B to apply multiplier
    temp_accumulator = {}
    
    # Part B: Configuration-based clamps (calculated for each existing side)
    _logger.info("  Part B - Configuration-based clamps:")
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    no_middle_columns_per_af = int(getattr(record, 'no_column_big_frame', 0))
    
    # Process each ASC side if it exists - collect in temp accumulator
    if getattr(record, 'front_span_asc', False):
        _calculate_front_span_asc_support_clamps(
            record, temp_accumulator, thick_column, no_anchor_frame_lines, no_middle_columns_per_af
        )
    
    if getattr(record, 'back_span_asc', False):
        _calculate_back_span_asc_support_clamps(
            record, temp_accumulator, thick_column, no_anchor_frame_lines, no_middle_columns_per_af
        )
    
    if getattr(record, 'front_bay_asc', False):
        _calculate_front_bay_asc_support_clamps(
            record, temp_accumulator, thick_column, no_anchor_frame_lines
        )
    
    if getattr(record, 'back_bay_asc', False):
        _calculate_back_bay_asc_support_clamps(
            record, temp_accumulator, thick_column, no_anchor_frame_lines
        )
    
    # Apply support_per_hockey multiplier to Part B and add to main accumulator
    for (clamp_type, size), quantity in temp_accumulator.items():
        final_quantity = quantity * support_per_hockey
        helpers.add_to_clamp_accumulator(accumulator, clamp_type, size, final_quantity)
        _logger.info(f"    {clamp_type} - {size}: {quantity} × {support_per_hockey} = {final_quantity}")


def _should_calculate_asc_support_clamps(record):
    """Check if ASC Support clamps should be calculated"""
    # Calculate if we have ASC Support components or any ASC sides active
    has_asc_support = _get_total_asc_support_pipe_count(record) > 0
    has_asc_sides = (
        getattr(record, 'front_span_asc', False) or
        getattr(record, 'back_span_asc', False) or
        getattr(record, 'front_bay_asc', False) or
        getattr(record, 'back_bay_asc', False)
    )
    return has_asc_support or has_asc_sides


def _get_total_asc_support_pipe_count(record):
    """
    Get the TOTAL count of ASC Support Pipes across ALL sides
    This sums up ASC Support components from all four sides
    """
    total_count = 0
    
    if hasattr(record, 'asc_component_ids'):
        # Get all ASC Support Pipe components
        asc_support = record.asc_component_ids.filtered(
            lambda c: 'ASC Support' in c.name or 'ASC Pipe Support' in c.name
        )
        if asc_support:
            total_count = sum(asc_support.mapped('nos'))
    
    _logger.info(f"    Total ASC Support Pipe count from all sides: {total_count}")
    return total_count


def _calculate_front_span_asc_support_clamps(record, accumulator, thick_column, af_lines, middle_cols_per_af):
    """Calculate Front Span ASC Support clamps - Part B"""
    _logger.info("  Front Span ASC Support:")
    
    if thick_column in ['1', '2']:  # 4 Corner OR 2 Bay Side
        # Thick Column clamps
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
            _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
        
        # AF/Main Column logic
        if af_lines >= 1:
            # Middle Columns
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and middle_cols_per_af > 0:
                qty = record.no_of_spans * middle_cols_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
            
            # AF Main Columns
            af_main_size = helpers.get_af_column_pipe_size(record)
            if af_main_size:
                qty = record.no_of_spans - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
        else:
            # Main Columns only
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_spans - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['3', '4']:  # 2 Span Side OR All 4 Side
        # Thick Column clamps
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            qty = record.no_of_spans + 1
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
            _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
        
        # Middle Columns if AF Lines exist
        if af_lines >= 1:
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and middle_cols_per_af > 0:
                qty = record.no_of_spans * middle_cols_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
    
    else:  # thick_column == '0'
        if af_lines > 0:
            # Middle Columns
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and middle_cols_per_af > 0:
                qty = record.no_of_spans * middle_cols_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
            
            # AF Main Columns
            af_main_size = helpers.get_af_column_pipe_size(record)
            if af_main_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
        else:
            # Main Columns only
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")


def _calculate_back_span_asc_support_clamps(record, accumulator, thick_column, af_lines, middle_cols_per_af):
    """Calculate Back Span ASC Support clamps - Part B"""
    _logger.info("  Back Span ASC Support:")
    
    if thick_column in ['1', '2']:  # 4 Corner OR 2 Bay Side
        # Thick Column clamps
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
            _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
        
        # AF/Main Column logic - Note: Back Span uses AF Lines >= 2
        if af_lines >= 2:
            # Middle Columns
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and middle_cols_per_af > 0:
                qty = record.no_of_spans * middle_cols_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
            
            # AF Main Columns
            af_main_size = helpers.get_af_column_pipe_size(record)
            if af_main_size:
                qty = record.no_of_spans - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
        else:
            # Main Columns only
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_spans - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['3', '4']:  # 2 Span Side OR All 4 Side
        # Thick Column clamps
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            qty = record.no_of_spans + 1
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
            _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
        
        # Middle Columns if AF Lines > 1 (different from Front Span)
        if af_lines > 1:
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and middle_cols_per_af > 0:
                qty = record.no_of_spans * middle_cols_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
    
    else:  # thick_column == '0'
        if af_lines > 1:
            # Middle Columns
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and middle_cols_per_af > 0:
                qty = record.no_of_spans * middle_cols_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {middle_size} (Middle)")
            
            # AF Main Columns
            af_main_size = helpers.get_af_column_pipe_size(record)
            if af_main_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {af_main_size} (AF Main)")
        else:
            # Main Columns only
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")


def _calculate_front_bay_asc_support_clamps(record, accumulator, thick_column, af_lines):
    """Calculate Front Bay ASC Support clamps - Part B"""
    _logger.info("  Front Bay ASC Support:")
    
    if thick_column in ['1', '3']:  # 4 Corner OR 2 Span Side
        if af_lines < 3:
            # Thick Columns
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
            
            # Main Columns
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_bays - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
        
        else:  # af_lines >= 3
            # Thick Columns
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
            
            # AF Columns
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                qty_af = af_lines - 2
                if qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                    _logger.info(f"    {qty_af} × Full Clamp - {af_size} (AF)")
            
            # Main Columns
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty_main = (record.no_of_bays + 1) - af_lines
                if qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                    _logger.info(f"    {qty_main} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['2', '4']:  # 2 Bay Side OR All 4 Side
        # Thick Columns
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            qty = record.no_of_bays + 1
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
            _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
    
    else:  # thick_column == '0'
        if af_lines == 0:
            # Main Columns only
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_bays + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
        else:  # af_lines > 0
            # AF Columns
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_lines)
                _logger.info(f"    {af_lines} × Full Clamp - {af_size} (AF)")
            
            # Main Columns
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = (record.no_of_bays + 1) - af_lines
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")


def _calculate_back_bay_asc_support_clamps(record, accumulator, thick_column, af_lines):
    """Calculate Back Bay ASC Support clamps - Part B"""
    _logger.info("  Back Bay ASC Support:")
    
    # Logic is identical to Front Bay
    if thick_column in ['1', '3']:  # 4 Corner OR 2 Span Side
        if af_lines < 3:
            # Thick Columns
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
            
            # Main Columns
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_bays - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
        
        else:  # af_lines >= 3
            # Thick Columns
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"    2 × Full Clamp - {thick_size} (Thick)")
            
            # AF Columns
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                qty_af = af_lines - 2
                if qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                    _logger.info(f"    {qty_af} × Full Clamp - {af_size} (AF)")
            
            # Main Columns
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty_main = (record.no_of_bays + 1) - af_lines
                if qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                    _logger.info(f"    {qty_main} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['2', '4']:  # 2 Bay Side OR All 4 Side
        # Thick Columns
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            qty = record.no_of_bays + 1
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
            _logger.info(f"    {qty} × Full Clamp - {thick_size} (Thick)")
    
    else:  # thick_column == '0'
        if af_lines == 0:
            # Main Columns only
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_bays + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")
        else:  # af_lines > 0
            # AF Columns
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_lines)
                _logger.info(f"    {af_lines} × Full Clamp - {af_size} (AF)")
            
            # Main Columns
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = (record.no_of_bays + 1) - af_lines
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"    {qty} × Full Clamp - {main_size} (Main)")