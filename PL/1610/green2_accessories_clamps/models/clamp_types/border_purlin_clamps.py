"""
Border Purlin Clamp Calculations - Final Correct Implementation
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_border_purlin_clamps(record, accumulator):
    """Accumulate border purlin clamps with FULL specification support"""
    if int(record.bay_side_border_purlin or 0) > 0:
        _calculate_bay_side_border_clamps_spec(record, accumulator)
    
    if int(record.span_side_border_purlin or 0) > 0:
        _calculate_span_side_border_clamps_spec(record, accumulator)


def _calculate_bay_side_border_clamps_spec(record, accumulator):
    """Bay Side Border Purlin Clamps - Full specification implementation"""
    bay_side_border_purlin = int(record.bay_side_border_purlin)
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    
    _logger.info(f"=== BAY SIDE BORDER PURLIN CLAMPS ===")
    _logger.info(f"Bay Side Border Purlin: {bay_side_border_purlin}")
    _logger.info(f"Thick Column: {thick_column}")
    _logger.info(f"AF Lines: {no_anchor_frame_lines}")
    
    if hasattr(record, 'front_bay_asc') and record.front_bay_asc:
        _logger.info("Front Bay: ASC Present")
        _add_bay_border_clamps_with_asc(record, accumulator, bay_side_border_purlin, 'Front Bay')
    else:
        _logger.info("Front Bay: No ASC")
        _add_bay_border_clamps_without_asc(record, accumulator, bay_side_border_purlin, 
                                           thick_column, no_anchor_frame_lines, 'Front Bay')
    
    if hasattr(record, 'back_bay_asc') and record.back_bay_asc:
        _logger.info("Back Bay: ASC Present")
        _add_bay_border_clamps_with_asc(record, accumulator, bay_side_border_purlin, 'Back Bay')
    else:
        _logger.info("Back Bay: No ASC")
        _add_bay_border_clamps_without_asc(record, accumulator, bay_side_border_purlin, 
                                           thick_column, no_anchor_frame_lines, 'Back Bay')


def _add_bay_border_clamps_with_asc(record, accumulator, bay_side_border_purlin, side_label):
    """Bay side clamps when ASC is present - ALL use ASC pipe size only"""
    asc_size = helpers.get_asc_pipe_size(record)
    if not asc_size:
        _logger.warning(f"{side_label} ASC enabled but pipe size not found")
        return
    
    _logger.info(f"  {side_label}: Using ASC pipe for ALL clamps")
    
    # Half Clamps - ASC size
    half_qty = (record.no_of_bays - 1) * bay_side_border_purlin
    if half_qty > 0:
        helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
        _logger.info(f"    Half Clamps (ASC): {half_qty} × {asc_size}")
    
    # Full Clamps - ASC size
    full_qty = 2 * bay_side_border_purlin
    if full_qty > 0:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)
        _logger.info(f"    Full Clamps (ASC): {full_qty} × {asc_size}")


def _add_bay_border_clamps_without_asc(record, accumulator, bay_side_border_purlin, 
                                       thick_column, af_lines, side_label):
    """Bay side clamps when NO ASC - Full specification logic"""
    
    if thick_column in ['1', '3']:
        _logger.info(f"  {side_label}: Thick Column = 1 (4 Corner) or 3 (2 Span Side)")
        
        if af_lines in [0, 1, 2]:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                half_qty = (record.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
            
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        else:
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                half_qty_af = (af_lines - 2) * bay_side_border_purlin
                if half_qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                    _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
            
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                half_qty_main = (record.no_of_bays - 1 - (af_lines - 2)) * bay_side_border_purlin
                if half_qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty_main)
                    _logger.info(f"    Half Clamps (Main): {half_qty_main} × {main_size}")
            
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
    
    elif thick_column in ['2', '4']:
        _logger.info(f"  {side_label}: Thick Column = 2 (Bay Side) or 4 (All 4 Side)")
        
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            half_qty = (record.no_of_bays - 1) * bay_side_border_purlin
            if half_qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_size, half_qty)
                _logger.info(f"    Half Clamps (Thick): {half_qty} × {thick_size}")
            
            full_qty = 2 * bay_side_border_purlin
            if full_qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
    
    else:
        _logger.info(f"  {side_label}: Thick Column = 0 (None)")
        
        if af_lines == 0:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                half_qty = (record.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                
                full_qty = 2 * bay_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, full_qty)
                    _logger.info(f"    Full Clamps (Main): {full_qty} × {main_size}")
        
        elif af_lines == 1:
            af_size = helpers.get_af_column_pipe_size(record)
            main_size = helpers.get_main_column_pipe_size(record)
            
            if main_size:
                half_qty = (record.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
            
            if af_size:
                full_qty_af = 1 * bay_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty_af)
                _logger.info(f"    Full Clamps (AF): {full_qty_af} × {af_size}")
            
            if main_size:
                full_qty = 1 * bay_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, full_qty)
                _logger.info(f"    Full Clamps (Main): {full_qty} × {main_size}")
        
        elif af_lines == 2:
            af_size = helpers.get_af_column_pipe_size(record)
            main_size = helpers.get_main_column_pipe_size(record)
            
            if main_size:
                half_qty = (record.no_of_bays - 1) * bay_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
            
            if af_size:
                full_qty_af = 2 * bay_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty_af)
                _logger.info(f"    Full Clamps (AF): {full_qty_af} × {af_size}")
        
        else:
            af_size = helpers.get_af_column_pipe_size(record)
            main_size = helpers.get_main_column_pipe_size(record)
            
            if af_size:
                half_qty_af = (af_lines - 2) * bay_side_border_purlin
                if half_qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                    _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
            
            if main_size:
                half_qty_main = (record.no_of_bays - af_lines + 1) * bay_side_border_purlin
                if half_qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty_main)
                    _logger.info(f"    Half Clamps (Main): {half_qty_main} × {main_size}")
            
            if af_size:
                full_qty_af = 2 * bay_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty_af)
                _logger.info(f"    Full Clamps (AF): {full_qty_af} × {af_size}")


def _calculate_span_side_border_clamps_spec(record, accumulator):
    """SPECIFICATION IMPLEMENTATION: Span Side Border Purlin Clamps"""
    span_side_border_purlin = int(record.span_side_border_purlin)
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    
    _logger.info(f"=== SPAN SIDE BORDER PURLIN CLAMPS ===")
    _logger.info(f"Span Side Border Purlin: {span_side_border_purlin}")
    _logger.info(f"Thick Column: {thick_column}")
    _logger.info(f"AF Lines: {no_anchor_frame_lines}")
    
    if hasattr(record, 'front_span_asc') and record.front_span_asc:
        _logger.info("Front Span: ASC Present")
        _add_span_border_clamps_with_asc(record, accumulator, span_side_border_purlin, 
                                         no_anchor_frame_lines, 'Front Span', is_front=True)
    else:
        _logger.info("Front Span: No ASC")
        _add_span_border_clamps_without_asc(record, accumulator, span_side_border_purlin, 
                                            thick_column, no_anchor_frame_lines, 'Front Span', is_front=True)
    
    if hasattr(record, 'back_span_asc') and record.back_span_asc:
        _logger.info("Back Span: ASC Present")
        _add_span_border_clamps_with_asc(record, accumulator, span_side_border_purlin, 
                                         no_anchor_frame_lines, 'Back Span', is_front=False)
    else:
        _logger.info("Back Span: No ASC")
        _add_span_border_clamps_without_asc(record, accumulator, span_side_border_purlin, 
                                            thick_column, no_anchor_frame_lines, 'Back Span', is_front=False)


def _add_span_border_clamps_with_asc(record, accumulator, span_side_border_purlin, af_lines, side_label, is_front):
    """Span side clamps when ASC is present - ASC pipe size with middle columns"""
    asc_size = helpers.get_asc_pipe_size(record)
    if not asc_size:
        _logger.warning(f"{side_label} ASC enabled but pipe size not found")
        return
    
    _logger.info(f"  {side_label}: Using ASC pipe for edge clamps")
    
    # Determine threshold based on front or back span
    af_threshold = 0 if is_front else 1
    
    if af_lines <= af_threshold:
        # No middle columns
        half_qty = (record.no_of_spans - 1) * span_side_border_purlin
        if half_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
            _logger.info(f"    Half Clamps (ASC): {half_qty} × {asc_size}")
        
        full_qty = 2 * span_side_border_purlin
        if full_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)
            _logger.info(f"    Full Clamps (ASC): {full_qty} × {asc_size}")
    
    else:
        # Has middle columns
        half_qty = (record.no_of_spans - 1) * span_side_border_purlin
        if half_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', asc_size, half_qty)
            _logger.info(f"    Half Clamps (ASC): {half_qty} × {asc_size}")
        
        middle_size = helpers.get_middle_column_pipe_size(record)
        if middle_size:
            half_qty_middle = record.no_of_spans * span_side_border_purlin
            helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
            _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
        
        full_qty = 2 * span_side_border_purlin
        if full_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', asc_size, full_qty)
            _logger.info(f"    Full Clamps (ASC): {full_qty} × {asc_size}")


def _add_span_border_clamps_without_asc(record, accumulator, span_side_border_purlin, 
                                        thick_column, af_lines, side_label, is_front):
    """Span side clamps when NO ASC - Full specification logic"""
    
    # Determine threshold based on front or back span
    af_threshold = 0 if is_front else 1
    
    if thick_column == '1':
        _logger.info(f"  {side_label}: Thick Column = 1 (4 Corner)")
        
        if af_lines <= af_threshold:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                half_qty = (record.no_of_spans - 1) * span_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
            
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        else:
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                half_qty_af = (record.no_of_spans - 1) * span_side_border_purlin
                if half_qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                    _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
            
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size:
                half_qty_middle = record.no_of_spans * span_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
            
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
    
    elif thick_column == '2':
        _logger.info(f"  {side_label}: Thick Column = 2 (Bay Side)")
        
        if af_lines <= af_threshold:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                half_qty = (record.no_of_spans - 1) * span_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
            
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        else:
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                half_qty_af = (record.no_of_spans - 1) * span_side_border_purlin
                if half_qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                    _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
            
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size:
                half_qty_middle = record.no_of_spans * span_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
            
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                    _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
    
    elif thick_column in ['3', '4']:
        _logger.info(f"  {side_label}: Thick Column = 3 (Span Side) or 4 (All 4 Side)")
        
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            half_qty = (record.no_of_spans - 1) * span_side_border_purlin
            if half_qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', thick_size, half_qty)
                _logger.info(f"    Half Clamps (Thick): {half_qty} × {thick_size}")
            
            full_qty = 2 * span_side_border_purlin
            if full_qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, full_qty)
                _logger.info(f"    Full Clamps (Thick): {full_qty} × {thick_size}")
        
        if af_lines > af_threshold:
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size:
                half_qty_middle = record.no_of_spans * span_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
    
    else:
        _logger.info(f"  {side_label}: Thick Column = 0 (None)")
        
        if af_lines <= af_threshold:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                half_qty = (record.no_of_spans - 1) * span_side_border_purlin
                if half_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', main_size, half_qty)
                    _logger.info(f"    Half Clamps (Main): {half_qty} × {main_size}")
                
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, full_qty)
                    _logger.info(f"    Full Clamps (Main): {full_qty} × {main_size}")
        
        else:
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                half_qty_af = (record.no_of_spans - 1) * span_side_border_purlin
                if half_qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', af_size, half_qty_af)
                    _logger.info(f"    Half Clamps (AF): {half_qty_af} × {af_size}")
            
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size:
                half_qty_middle = record.no_of_spans * span_side_border_purlin
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_size, half_qty_middle)
                _logger.info(f"    Half Clamps (Middle): {half_qty_middle} × {middle_size}")
            
            if af_size:
                full_qty = 2 * span_side_border_purlin
                if full_qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, full_qty)
                    _logger.info(f"    Full Clamps (AF): {full_qty} × {af_size}")