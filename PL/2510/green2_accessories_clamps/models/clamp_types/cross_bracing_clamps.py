# green2_accessories_clamps/models/clamp_types/cross_bracing_clamps.py
"""
Cross Bracing Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_front_back_cross_bracing_clamps(record, accumulator):
    """Accumulate Front & Back Column to Column Cross Bracing X Clamps"""
    cross_bracing = record.lower_component_ids.filtered(
        lambda c: c.name == 'Front & Back Column to Column Cross Bracing X'
    )
    
    if not cross_bracing or cross_bracing.nos == 0:
        return
    
    cross_bracing_count = cross_bracing.nos
    af_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    thick_column = getattr(record, 'thick_column', '0')
    
    _logger.info(f"=== F&B CROSS BRACING CLAMPS ===")
    _logger.info(f"Cross Bracing count: {cross_bracing_count}")
    _logger.info(f"AF Lines: {af_lines}, Thick Column: {thick_column}")
    
    afx = 0
    if af_lines > 2:
        afx = min(af_lines - 2, 4)
        _logger.info(f"AFX calculated as {afx} (AF Lines: {af_lines})")
    
    main_size = helpers.get_main_column_pipe_size(record)
    af_size = helpers.get_af_column_pipe_size(record)
    thick_size = helpers.get_thick_column_pipe_size(record)
    
    if thick_column in ['1', '3', '0']:
        if afx == 0:
            if main_size:
                qty = cross_bracing_count * 2
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                _logger.info(f"  {qty} × Full Clamp - {main_size} (Main)")
        else:
            if af_size:
                qty_af = afx * 2 * (record.no_of_spans + 1)
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                _logger.info(f"  {qty_af} × Full Clamp - {af_size} (AF)")
            
            if main_size:
                qty_main = (cross_bracing_count * 2) - (afx * 2 * (record.no_of_spans + 1))
                if qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                    _logger.info(f"  {qty_main} × Full Clamp - {main_size} (Main)")
    
    elif thick_column in ['2', '4']:
        if afx == 0:
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 16)
                _logger.info(f"  16 × Full Clamp - {thick_size} (Thick)")
            
            if main_size:
                qty = (cross_bracing_count * 2) - 16
                if qty > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty)
                    _logger.info(f"  {qty} × Full Clamp - {main_size} (Main)")
        else:
            if thick_size:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, 16)
                _logger.info(f"  16 × Full Clamp - {thick_size} (Thick)")
            
            if af_size:
                qty_af = afx * 2 * (record.no_of_spans + 1)
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, qty_af)
                _logger.info(f"  {qty_af} × Full Clamp - {af_size} (AF)")
            
            if main_size:
                qty_main = (cross_bracing_count * 2) - (afx * 2 * (record.no_of_spans + 1)) - 16
                if qty_main > 0:
                    helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, qty_main)
                    _logger.info(f"  {qty_main} × Full Clamp - {main_size} (Main)")


def accumulate_internal_cc_cross_bracing_clamps(record, accumulator):
    """Accumulate Internal Column to Column Cross Bracing X Clamps"""
    internal_cc_bracing = record.lower_component_ids.filtered(
        lambda c: c.name == 'Internal CC Cross Bracing X'
    )
    
    if not internal_cc_bracing or internal_cc_bracing.nos == 0:
        return
    
    internal_cc_count = internal_cc_bracing.nos
    thick_column = getattr(record, 'thick_column', '0')
    af_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    afx2 = int(getattr(record, 'afx2_internal_cc_lines', 0))
    
    _logger.info(f"=== INTERNAL CC CROSS BRACING CLAMPS ===")
    _logger.info(f"Internal CC count: {internal_cc_count}")
    _logger.info(f"Thick Column: {thick_column}, AF Lines: {af_lines}, AFX2: {afx2}")
    
    thick_size = helpers.get_thick_column_pipe_size(record)
    af_size = helpers.get_af_column_pipe_size(record)
    main_size = helpers.get_main_column_pipe_size(record)
    
    thick_clamp_count = 0
    af_clamp_count = 0
    main_clamp_count = 0
    
    if thick_column in ['2', '4']:
        if thick_size:
            thick_clamp_count = 8 * internal_cc_count
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, thick_clamp_count)
            _logger.info(f"  {thick_clamp_count} × Full Clamp - {thick_size} (Thick)")
    
    if af_lines > 2 and afx2 > 0:
        if af_size:
            af_clamp_count = (afx2 * (record.no_of_spans + 1)) * 2
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_clamp_count)
            _logger.info(f"  {af_clamp_count} × Full Clamp - {af_size} (AF)")
        
        if main_size:
            total_needed = internal_cc_count * 2
            main_clamp_count = total_needed - thick_clamp_count - af_clamp_count
            if main_clamp_count > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, main_clamp_count)
                _logger.info(f"  {main_clamp_count} × Full Clamp - {main_size} (Main)")
    elif thick_column not in ['2', '4']:
        if main_size:
            main_clamp_count = internal_cc_count * 2
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, main_clamp_count)
            _logger.info(f"  {main_clamp_count} × Full Clamp - {main_size} (Main)")


def accumulate_cross_bracing_column_arch_clamps(record, accumulator):
    """Accumulate Cross Bracing Column to Arch Clamps"""
    cross_bracing_arch = record.lower_component_ids.filtered(
        lambda c: c.name == 'Cross Bracing Column to Arch'
    )
    
    if not cross_bracing_arch or cross_bracing_arch.nos == 0:
        return
    
    cross_bracing_count = cross_bracing_arch.nos
    thick_column = getattr(record, 'thick_column', '0')
    af_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    afx3 = int(getattr(record, 'afx3_column_arch_lines', 0)) if af_lines > 2 else 0
    
    _logger.info(f"=== COLUMN TO ARCH BRACING CLAMPS ===")
    _logger.info(f"Cross Bracing count: {cross_bracing_count}")
    _logger.info(f"Thick Column: {thick_column}, AF Lines: {af_lines}, AFX3: {afx3}")
    
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    
    if big_arch_data['size']:
        big_arch_qty = cross_bracing_count // 2
        if big_arch_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], big_arch_qty)
            _logger.info(f"  {big_arch_qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
    
    if small_arch_data['size']:
        small_arch_qty = cross_bracing_count // 2
        if small_arch_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], small_arch_qty)
            _logger.info(f"  {small_arch_qty} × Full Clamp - {small_arch_data['size']} (Small Arch)")
    
    thick_size = helpers.get_thick_column_pipe_size(record)
    af_size = helpers.get_af_column_pipe_size(record)
    main_size = helpers.get_main_column_pipe_size(record)
    
    thick_clamp_count = 0
    af_clamp_count = 0
    
    if thick_column in ['2', '4']:
        if thick_size:
            thick_clamp_count = 4
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, thick_clamp_count)
            _logger.info(f"  {thick_clamp_count} × Full Clamp - {thick_size} (Thick)")
        
        if afx3 > 0 and af_size:
            af_clamp_count = afx3 * ((record.no_of_spans * 2) - 2)
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_clamp_count)
            _logger.info(f"  {af_clamp_count} × Full Clamp - {af_size} (AF)")
    else:
        if afx3 > 0 and af_size:
            af_clamp_count = afx3 * (record.no_of_spans * 2)
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_clamp_count)
            _logger.info(f"  {af_clamp_count} × Full Clamp - {af_size} (AF)")
    
    if main_size:
        main_clamp_count = cross_bracing_count - af_clamp_count - thick_clamp_count
        if main_clamp_count > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, main_clamp_count)
            _logger.info(f"  {main_clamp_count} × Full Clamp - {main_size} (Main)")


def accumulate_cross_bracing_column_bottom_clamps(record, accumulator):
    """Accumulate Cross Bracing Column to Bottom Chord Clamps"""
    cross_bracing_bottom = record.lower_component_ids.filtered(
        lambda c: c.name == 'Cross Bracing Column to Bottom Chord'
    )
    
    if not cross_bracing_bottom or cross_bracing_bottom.nos == 0:
        return
    
    cross_bracing_count = cross_bracing_bottom.nos
    thick_column = getattr(record, 'thick_column', '0')
    af_lines = int(getattr(record, 'no_anchor_frame_lines', 0))
    afx4 = int(getattr(record, 'afx4_column_bottom_lines', 0)) if af_lines > 2 else 0
    
    _logger.info(f"=== COLUMN TO BOTTOM CHORD BRACING CLAMPS ===")
    _logger.info(f"Cross Bracing count: {cross_bracing_count}")
    _logger.info(f"Thick Column: {thick_column}, AF Lines: {af_lines}, AFX4: {afx4}")
    
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    if bottom_chord_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], cross_bracing_count)
        _logger.info(f"  {cross_bracing_count} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
    
    thick_size = helpers.get_thick_column_pipe_size(record)
    af_size = helpers.get_af_column_pipe_size(record)
    main_size = helpers.get_main_column_pipe_size(record)
    
    thick_clamp_count = 0
    af_clamp_count = 0
    
    if thick_column in ['2', '4']:
        if thick_size:
            thick_clamp_count = 4
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', thick_size, thick_clamp_count)
            _logger.info(f"  {thick_clamp_count} × Full Clamp - {thick_size} (Thick)")
        
        if afx4 > 0 and af_size:
            af_clamp_count = afx4 * ((record.no_of_spans * 2) - 2)
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_clamp_count)
            _logger.info(f"  {af_clamp_count} × Full Clamp - {af_size} (AF)")
    else:
        if afx4 > 0 and af_size:
            af_clamp_count = afx4 * (record.no_of_spans * 2)
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', af_size, af_clamp_count)
            _logger.info(f"  {af_clamp_count} × Full Clamp - {af_size} (AF)")
    
    if main_size:
        main_clamp_count = cross_bracing_count - af_clamp_count - thick_clamp_count
        if main_clamp_count > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', main_size, main_clamp_count)
            _logger.info(f"  {main_clamp_count} × Full Clamp - {main_size} (Main)")


def accumulate_cross_bracing_clamps(record, accumulator):
    """Backward compatibility wrapper"""
    return accumulate_front_back_cross_bracing_clamps(record, accumulator)
