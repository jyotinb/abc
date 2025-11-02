# green2_accessories_clamps/models/clamp_types/purlin_clamps.py
"""
Purlin Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_purlin_clamps(record, accumulator):
    """Accumulate purlin clamps"""
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    
    _logger.info("=== PURLIN CLAMPS ===")
    
    if big_arch_data['count'] > 0 and big_arch_data['size']:
        if record.big_purlin_clamp_type_first:
            qty_first = record.no_of_spans * 2
            clamp_name = 'Full Clamp' if record.big_purlin_clamp_type_first == 'full_clamp' else 'L Joint'
            helpers.add_to_clamp_accumulator_separate(
                accumulator, f"{clamp_name} (Big Arch Purlin)", big_arch_data['size'], qty_first)
            _logger.info(f"  {qty_first} × {clamp_name} - {big_arch_data['size']} (Big Arch Purlin First)")
            
            if record.big_purlin_clamp_type_second:
                qty_second = big_arch_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = ('Half Clamp' if record.big_purlin_clamp_type_second == 'half_clamp' 
                                 else 'T Joint')
                    helpers.add_to_clamp_accumulator_separate(
                        accumulator, f"{clamp_name} (Big Arch Purlin)", big_arch_data['size'], qty_second)
                    _logger.info(f"  {qty_second} × {clamp_name} - {big_arch_data['size']} (Big Arch Purlin Second)")
    
    if small_arch_data['count'] > 0 and small_arch_data['size']:
        if record.small_purlin_clamp_type_first:
            qty_first = record.no_of_spans * 2
            clamp_name = ('Full Clamp' if record.small_purlin_clamp_type_first == 'full_clamp' 
                         else 'L Joint')
            helpers.add_to_clamp_accumulator_separate(
                accumulator, f"{clamp_name} (Small Arch Purlin)", small_arch_data['size'], qty_first)
            _logger.info(f"  {qty_first} × {clamp_name} - {small_arch_data['size']} (Small Arch Purlin First)")
            
            if record.small_purlin_clamp_type_second:
                qty_second = small_arch_data['count'] - qty_first
                if qty_second > 0:
                    clamp_name = ('Half Clamp' if record.small_purlin_clamp_type_second == 'half_clamp' 
                                 else 'T Joint')
                    helpers.add_to_clamp_accumulator_separate(
                        accumulator, f"{clamp_name} (Small Arch Purlin)", small_arch_data['size'], qty_second)
                    _logger.info(f"  {qty_second} × {clamp_name} - {small_arch_data['size']} (Small Arch Purlin Second)")
