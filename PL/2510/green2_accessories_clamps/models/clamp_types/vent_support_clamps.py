# green2_accessories_clamps/models/clamp_types/vent_support_clamps.py
"""
Vent Support Small Arch Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_vent_support_small_arch_clamps(record, accumulator):
    """Accumulate clamps for Vent Support for Small Arch"""
    vent_small_support = record.truss_component_ids.filtered(
        lambda c: c.name == 'Vent Support for Small Arch')
    
    if not vent_small_support or vent_small_support.nos == 0:
        return
    
    vent_count = vent_small_support.nos
    _logger.info(f"=== VENT SUPPORT SMALL ARCH CLAMPS ===")
    _logger.info(f"Vent Support count: {vent_count}")
    
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    if bottom_chord_data['size']:
        qty = vent_count // 2
        if qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
            _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
    
    small_arch_purlin_size = helpers.get_small_arch_purlin_size(record)
    if small_arch_purlin_size:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_purlin_size, vent_count)
        _logger.info(f"  {vent_count} × Full Clamp - {small_arch_purlin_size} (Small Arch Purlin)")
