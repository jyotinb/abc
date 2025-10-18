# green2_accessories_clamps/models/clamp_types/asc_clamps.py
"""
ASC (Additional Side Corridor) Clamp Calculations
- F Bracket Mode
- Gutter Arch Bracket Mode
- Default Mode (when no bracket type selected)
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_asc_clamps_complete(record, accumulator):
    """
    Complete ASC clamp logic based on document specifications
    Handles F Brackets and Gutter Arch Brackets with full configuration
    """
    gutter_bracket_type = getattr(record, 'gutter_bracket_type', 'none')
    
    if gutter_bracket_type == 'f_bracket':
        _accumulate_asc_clamps_f_bracket(record, accumulator)
    elif gutter_bracket_type == 'arch':
        _accumulate_asc_clamps_gutter_arch(record, accumulator)
    else:
        has_asc = (record.front_span_asc or record.back_span_asc or 
                   record.front_bay_asc or record.back_bay_asc)
        
        if has_asc:
            _logger.warning("⚠️ ASC is enabled but Gutter Bracket Type is 'None'. "
                           "Calculating clamps for ALL present ASC sides (conservative approach).")
            _accumulate_asc_clamps_default(record, accumulator)


def _accumulate_asc_clamps_f_bracket(record, accumulator):
    """ASC Clamps for F Brackets - FIXED to use correct middle column size"""
    _logger.info("=== ASC CLAMPS: F BRACKET MODE ===")
    
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    no_middle_columns_per_af = int(getattr(record, 'no_column_big_frame', 0))
    
    # FRONT SPAN ASC
    if record.front_span_asc:
        _logger.info("Processing Front Span ASC (F Bracket)")
        
        if thick_column in ['1', '2']:  # 4 Corner or 2 Bay Side
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"  Front Span: 2 × Full Clamp - {thick_size} (Thick)")
            
            if no_anchor_frame_lines >= 1:
                # FIXED: Using middle column size for middle columns
                middle_size = helpers.get_middle_column_pipe_size(record)
                if middle_size and no_middle_columns_per_af > 0:
                    qty = record.no_of_spans * no_middle_columns_per_af
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"  Front Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                
                af_main_size = helpers.get_af_column_pipe_size(record)
                if af_main_size:
                    qty = record.no_of_spans - 1
                    if qty > 0:
                        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                main_size = helpers.get_main_column_pipe_size(record)
                if main_size:
                    qty = record.no_of_spans - 1
                    if qty > 0:
                        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                        _logger.info(f"  Front Span: {qty} × Full Clamp - {main_size} (Main)")
        
        elif thick_column in ['3', '4']:  # 2 Span Side or All 4 Side
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
                _logger.info(f"  Front Span: {qty} × Full Clamp - {thick_size} (Thick)")
            
            if no_anchor_frame_lines >= 1:
                # FIXED: Using middle column size for middle columns
                middle_size = helpers.get_middle_column_pipe_size(record)
                if middle_size and no_middle_columns_per_af > 0:
                    qty = record.no_of_spans * no_middle_columns_per_af
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"  Front Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
        
        else:  # thick_column == '0'
            if no_anchor_frame_lines > 0:
                # FIXED: Using middle column size for middle columns
                middle_size = helpers.get_middle_column_pipe_size(record)
                if middle_size and no_middle_columns_per_af > 0:
                    qty = record.no_of_spans * no_middle_columns_per_af
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                    _logger.info(f"  Front Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
                
                af_main_size = helpers.get_af_column_pipe_size(record)
                if af_main_size:
                    qty = record.no_of_spans + 1
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"  Front Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
            else:
                main_size = helpers.get_main_column_pipe_size(record)
                if main_size:
                    qty = record.no_of_spans + 1
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  Front Span: {qty} × Full Clamp - {main_size} (Main)")
    
    # BACK SPAN ASC (similar logic with AF Lines >= 2 check)
    if record.back_span_asc:
        _logger.info("Processing Back Span ASC (F Bracket)")
        _accumulate_asc_clamps_f_bracket_span_logic(record, accumulator, 'back', 2)
    
    # FRONT BAY ASC (F Bracket mode)
    if record.front_bay_asc:
        _logger.info("Processing Front Bay ASC (F Bracket)")
        _process_bay_asc_f_bracket(record, accumulator, 'front', thick_column, no_anchor_frame_lines)
    
    # BACK BAY ASC (F Bracket mode)
    if record.back_bay_asc:
        _logger.info("Processing Back Bay ASC (F Bracket)")
        _process_bay_asc_f_bracket(record, accumulator, 'back', thick_column, no_anchor_frame_lines)


def _accumulate_asc_clamps_f_bracket_span_logic(record, accumulator, side, af_check):
    """Reusable span logic for F Bracket and Gutter Arch - FIXED for middle column size"""
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    no_middle_columns_per_af = int(getattr(record, 'no_column_big_frame', 0))
    side_label = side.title()
    
    _logger.info(f"Processing {side_label} Span ASC")
    
    if thick_column in ['1', '2']:  # 4 Corner or 2 Bay Side
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
            _logger.info(f"  {side_label} Span: 2 × Full Clamp - {thick_size} (Thick)")
        
        if no_anchor_frame_lines >= af_check:
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and no_middle_columns_per_af > 0:
                qty = record.no_of_spans * no_middle_columns_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
            
            af_main_size = helpers.get_af_column_pipe_size(record)
            if af_main_size:
                qty = record.no_of_spans - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
        else:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_spans - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['3', '4']:  # 2 Span Side or All 4 Side
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            qty = record.no_of_spans + 1
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
            _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {thick_size} (Thick)")
        
        if no_anchor_frame_lines >= af_check:
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and no_middle_columns_per_af > 0:
                qty = record.no_of_spans * no_middle_columns_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
    
    else:  # thick_column == '0'
        if no_anchor_frame_lines >= af_check:
            middle_size = helpers.get_middle_column_pipe_size(record)
            if middle_size and no_middle_columns_per_af > 0:
                qty = record.no_of_spans * no_middle_columns_per_af
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_size, qty)
                _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {middle_size} (Middle Columns in AF)")
            
            af_main_size = helpers.get_af_column_pipe_size(record)
            if af_main_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_main_size, qty)
                _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {af_main_size} (AF Main)")
        else:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_spans + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"  {side_label} Span: {qty} × Full Clamp - {main_size} (Main)")


def _process_bay_asc_f_bracket(record, accumulator, side, thick_column, af_lines):
    """Process Bay ASC for F Bracket mode"""
    side_label = side.title()
    
    if thick_column in ['1', '3']:  # 4 Corner or 2 Span Side
        if af_lines < 3:
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"  {side_label} Bay: 2 × Full Clamp - {thick_size} (Thick)")
            
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_bays - 1
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {main_size} (Main)")
        else:
            thick_size = helpers.get_thick_column_pipe_size(record)
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 2)
                _logger.info(f"  {side_label} Bay: 2 × Full Clamp - {thick_size} (Thick)")
            
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                qty_af = af_lines - 2
                if qty_af > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                    _logger.info(f"  {side_label} Bay: {qty_af} × Full Clamp - {af_size} (AF)")
            
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty_main = (record.no_of_bays + 1) - af_lines
                if qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                    _logger.info(f"  {side_label} Bay: {qty_main} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['2', '4']:  # 2 Bay Side or All 4 Side
        thick_size = helpers.get_thick_column_pipe_size(record)
        if thick_size:
            qty = record.no_of_bays + 1
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, qty)
            _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {thick_size} (Thick)")
    
    else:  # thick_column == '0'
        if af_lines == 0:
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = record.no_of_bays + 1
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {main_size} (Main)")
        else:
            af_size = helpers.get_af_column_pipe_size(record)
            if af_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_lines)
                _logger.info(f"  {side_label} Bay: {af_lines} × Full Clamp - {af_size} (AF)")
            
            main_size = helpers.get_main_column_pipe_size(record)
            if main_size:
                qty = (record.no_of_bays + 1) - af_lines
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  {side_label} Bay: {qty} × Full Clamp - {main_size} (Main)")


def _accumulate_asc_clamps_gutter_arch(record, accumulator):
    """ASC Clamps for Gutter Arch Brackets"""
    bay_side_required = getattr(record, 'bay_side_clamp_required', False)
    
    _logger.info(f"=== ASC CLAMPS: GUTTER ARCH BRACKET MODE (Bay Side Required: {bay_side_required}) ===")
    
    # Process span sides (same logic as F Bracket)
    if record.front_span_asc:
        _accumulate_asc_clamps_f_bracket_span_logic(record, accumulator, 'front', 1)
    
    if record.back_span_asc:
        _accumulate_asc_clamps_f_bracket_span_logic(record, accumulator, 'back', 2)
    
    # Process bay sides only if required
    if bay_side_required:
        thick_column = getattr(record, 'thick_column', '0')
        no_anchor_frame_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
        
        if record.front_bay_asc:
            _logger.info("Processing Front Bay ASC (Gutter Arch - Bay Side Required)")
            _process_bay_asc_f_bracket(record, accumulator, 'front', thick_column, no_anchor_frame_lines)
        
        if record.back_bay_asc:
            _logger.info("Processing Back Bay ASC (Gutter Arch - Bay Side Required)")
            _process_bay_asc_f_bracket(record, accumulator, 'back', thick_column, no_anchor_frame_lines)


def _accumulate_asc_clamps_default(record, accumulator):
    """ASC Clamps when no bracket type is selected - use F Bracket logic for all sides"""
    _logger.info("=== ASC CLAMPS: DEFAULT MODE (Using F Bracket logic for all sides) ===")
    _accumulate_asc_clamps_f_bracket(record, accumulator)