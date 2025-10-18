# green2_accessories_clamps/models/clamp_types/m_type_clamps.py
"""
M Type Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_m_type_clamps(record, accumulator):
    """Accumulate M Type clamps"""
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    bottom_chord_anchor_data = helpers.get_bottom_chord_anchor_data(record)
    v_support_count = helpers.get_v_support_count(record)
    v_support_for_af = getattr(record, 'v_support_for_af', True)
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    vent_big_support_count = helpers.get_vent_big_support_count(record)
    middle_column_data = helpers.get_middle_column_data(record)
    
    _logger.info(f"=== M TYPE CLAMPS (Bottom Chord Type: {record.bottom_chord_clamp_type}) ===")
    
    # Bottom Chord (Non-Anchor)
    if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
        # Calculate v_support adjustment
        if v_support_for_af:
            v_support_adjustment = v_support_count - (2 * bottom_chord_anchor_data['count'])
            v_support_adjustment = max(0, v_support_adjustment)  # Don't go negative
        else:
            v_support_adjustment = v_support_count
        
        if record.bottom_chord_clamp_type == 'single':
            qty = (bottom_chord_data['count'] * 3) + v_support_adjustment
        else:
            qty = (bottom_chord_data['count'] * 5) + v_support_adjustment
        
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
    
    # Bottom Chord Anchor
    if bottom_chord_anchor_data['count'] > 0 and bottom_chord_anchor_data['size']:
        multiplier = 4 if v_support_for_af else 2
        qty = bottom_chord_anchor_data['count'] * multiplier
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                        bottom_chord_anchor_data['size'], qty)
        _logger.info(f"  {qty} × Full Clamp - {bottom_chord_anchor_data['size']} (Bottom Chord Anchor)")
    
    # ... rest of the code remains same (Big Arch, Small Arch, Middle Column)
    
    if big_arch_data['count'] > 0 and big_arch_data['size']:
        qty = (big_arch_data['count'] * 2) + vent_big_support_count
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
    
    if small_arch_data['count'] > 0 and small_arch_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], 
                                      small_arch_data['count'])
        _logger.info(f"  {small_arch_data['count']} × Full Clamp - {small_arch_data['size']} (Small Arch)")
    
    if middle_column_data['count'] > 0 and middle_column_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_column_data['size'], 
                                      middle_column_data['count'])
        helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_column_data['size'], 
                                      middle_column_data['count'])
        _logger.info(f"  {middle_column_data['count']} × Full Clamp - {middle_column_data['size']} (Middle Column)")
        _logger.info(f"  {middle_column_data['count']} × Half Clamp - {middle_column_data['size']} (Middle Column)")
