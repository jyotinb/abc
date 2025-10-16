# green2_accessories_clamps/models/clamp_types/gable_purlin_clamps.py
"""
Gable Purlin Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_gable_purlin_clamps(record, accumulator):
    """Accumulate Gable Purlin Clamps (only for F Bracket configuration)"""
    gable_purlin = record.truss_component_ids.filtered(lambda c: c.name == 'Gable Purlin')
    
    if not gable_purlin or gable_purlin.nos == 0:
        return
    
    gutter_bracket_type = getattr(record, 'gutter_bracket_type', 'none')
    
    if gutter_bracket_type != 'f_bracket':
        _logger.info("Gable Purlin exists but not F Bracket configuration - skipping Gable Purlin clamps")
        return
    
    _logger.info(f"=== GABLE PURLIN CLAMPS (F Bracket) ===")
    _logger.info(f"Gable Purlin count: {gable_purlin.nos}")
    
    big_arch_data = helpers.get_big_arch_data(record)
    
    if big_arch_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], 4)
        _logger.info(f"  4 × Full Clamp - {big_arch_data['size']} (Big Arch)")
        
        half_qty = (record.no_of_bays - 1) * 2
        if half_qty > 0:
            helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', big_arch_data['size'], half_qty)
            _logger.info(f"  {half_qty} × Half Clamp - {big_arch_data['size']} (Big Arch)")
