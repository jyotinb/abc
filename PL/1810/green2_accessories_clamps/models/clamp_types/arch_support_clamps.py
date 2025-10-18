# green2_accessories_clamps/models/clamp_types/arch_support_clamps.py
"""
Arch Support Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_arch_2_bottom_clamps(record, accumulator):
    """Accumulate clamps for Arch to Bottom Support"""
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    small_arch_support_count = helpers.get_small_arch_support_count(record)
    
    _logger.info("=== ARCH TO BOTTOM CLAMPS ===")
    
    if small_arch_support_count > 0:
        if bottom_chord_data['size']:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                          bottom_chord_data['size'], small_arch_support_count)
            _logger.info(f"  {small_arch_support_count} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
        
        if big_arch_data['size']:
            qty = small_arch_support_count // 2
            if qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              big_arch_data['size'], qty)
                _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
        
        if small_arch_data['size']:
            qty = small_arch_support_count // 2
            if qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              small_arch_data['size'], qty)
                _logger.info(f"  {qty} × Full Clamp - {small_arch_data['size']} (Small Arch)")
    
    arch_support_straight_middle_data = helpers.get_arch_support_straight_middle_data(record)
    if arch_support_straight_middle_data['count'] > 0:
        if bottom_chord_data['size']:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                          bottom_chord_data['size'], 
                                          arch_support_straight_middle_data['count'])
            _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                        f"{bottom_chord_data['size']} (Bottom Chord for Straight Middle)")
        
        if big_arch_data['size']:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                          big_arch_data['size'], 
                                          arch_support_straight_middle_data['count'])
            _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                        f"{big_arch_data['size']} (Big Arch for Straight Middle)")


def accumulate_arch_2_straight_clamps(record, accumulator):
    """Accumulate clamps for Arch to Straight Middle"""
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    big_arch_support_count = helpers.get_big_arch_support_count(record)
    
    _logger.info("=== ARCH TO STRAIGHT MIDDLE CLAMPS ===")
    
    if big_arch_support_count > 0:
        if bottom_chord_data['size']:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                          bottom_chord_data['size'], big_arch_support_count)
            _logger.info(f"  {big_arch_support_count} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
        
        if big_arch_data['size']:
            qty = big_arch_support_count // 2
            if qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              big_arch_data['size'], qty)
                _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
        
        if small_arch_data['size']:
            qty = big_arch_support_count // 2
            if qty > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                              small_arch_data['size'], qty)
                _logger.info(f"  {qty} × Full Clamp - {small_arch_data['size']} (Small Arch)")
    
    arch_support_straight_middle_data = helpers.get_arch_support_straight_middle_data(record)
    if arch_support_straight_middle_data['count'] > 0 and big_arch_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                      big_arch_data['size'], 
                                      arch_support_straight_middle_data['count'])
        _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                    f"{big_arch_data['size']} (Big Arch for Straight Middle)")
