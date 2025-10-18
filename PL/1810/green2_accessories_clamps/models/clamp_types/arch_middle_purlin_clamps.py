# green2_accessories_clamps/models/clamp_types/arch_middle_purlin_clamps.py
"""
Arch Middle Purlin Clamp Calculations
"""

import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_arch_middle_purlin_clamps(record, accumulator):
    """Accumulate Arch Middle Purlin clamps for both Big and Small Arch"""
    _logger.info("=== ARCH MIDDLE PURLIN CLAMPS ===")
    
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    
    arch_middle_purlin_big_arch = getattr(record, 'arch_middle_purlin_big_arch', '0')
    arch_middle_purlin_big_arch_pcs = int(getattr(record, 'arch_middle_purlin_big_arch_pcs', 0))
    arch_middle_purlin_small_arch = getattr(record, 'arch_middle_purlin_small_arch', '0')
    arch_middle_purlin_small_arch_pcs = int(getattr(record, 'arch_middle_purlin_small_arch_pcs', 0))
    
    big_arch_purlin_count = _get_arch_middle_purlin_count(record, 'big')
    small_arch_purlin_count = _get_arch_middle_purlin_count(record, 'small')
    
    if arch_middle_purlin_big_arch != '0' and big_arch_data['size'] and big_arch_purlin_count > 0:
        _logger.info(f"Processing Big Arch Middle Purlin - Config: {arch_middle_purlin_big_arch}, Pcs: {arch_middle_purlin_big_arch_pcs}")
        _calculate_arch_middle_purlin_clamps_for_type(
            record, accumulator, 'big', big_arch_data['size'], 
            arch_middle_purlin_big_arch, arch_middle_purlin_big_arch_pcs, big_arch_purlin_count
        )
    
    if arch_middle_purlin_small_arch != '0' and small_arch_data['size'] and small_arch_purlin_count > 0:
        _logger.info(f"Processing Small Arch Middle Purlin - Config: {arch_middle_purlin_small_arch}, Pcs: {arch_middle_purlin_small_arch_pcs}")
        _calculate_arch_middle_purlin_clamps_for_type(
            record, accumulator, 'small', small_arch_data['size'], 
            arch_middle_purlin_small_arch, arch_middle_purlin_small_arch_pcs, small_arch_purlin_count
        )


def _get_arch_middle_purlin_count(record, arch_type):
    """Get the count of Arch Middle Purlin components from truss_component_ids"""
    if arch_type == 'big':
        component_name = 'Arch Middle Purlin Big Arch'
    else:
        component_name = 'Arch Middle Purlin Small Arch'
    
    purlin_component = record.truss_component_ids.filtered(lambda c: c.name == component_name)
    return purlin_component.nos if purlin_component else 0


def _calculate_arch_middle_purlin_clamps_for_type(record, accumulator, arch_type, arch_size, 
                                                   config_type, pcs_count, total_purlin_count):
    """Calculate clamps for a specific arch middle purlin type"""
    arch_label = "Big Arch" if arch_type == 'big' else "Small Arch"
    no_of_spans = record.no_of_spans
    no_of_bays = record.no_of_bays
    
    full_clamp_count = 0
    half_clamp_count = 0
    
    # Config 1: 4 Corners
    if config_type == '1':
        full_clamp_count = total_purlin_count * 2
        _logger.info(f"  {arch_label} (4 Corners): Full = {full_clamp_count}")
    
    # Config 2: Front & Back
    elif config_type == '2':
        full_clamp_count = total_purlin_count * 2
        _logger.info(f"  {arch_label} (Front & Back): Full = {full_clamp_count}")
    
    # Config 3: Both Side
    elif config_type == '3':
        full_clamp_count = 4 * pcs_count
        half_clamp_count = (no_of_bays - 1) * pcs_count * 2
        _logger.info(f"  {arch_label} (Both Side): Full = {full_clamp_count}, Half = {half_clamp_count}")
    
    # Config 4: 4 Side
    elif config_type == '4':
        full_clamp_count = ((((no_of_spans - 2) * 4) + 4) * pcs_count)
        half_clamp_count = (no_of_bays - 1) * pcs_count * 2
        _logger.info(f"  {arch_label} (4 Side): Full = {full_clamp_count}, Half = {half_clamp_count}")
    
    # Config 5: All
    elif config_type == '5':
        full_clamp_count = no_of_spans * 2 * pcs_count
        half_clamp_count = no_of_spans * (no_of_bays - 1) * pcs_count
        _logger.info(f"  {arch_label} (All): Full = {full_clamp_count}, Half = {half_clamp_count}")
    
    # Add to accumulator
    if full_clamp_count > 0:
        component_name = f"Full Clamp (Arch Middle Purlin {arch_label})"
        helpers.add_to_clamp_accumulator_separate(accumulator, component_name, arch_size, full_clamp_count)
    
    if half_clamp_count > 0:
        component_name = f"Half Clamp (Arch Middle Purlin {arch_label})"
        helpers.add_to_clamp_accumulator_separate(accumulator, component_name, arch_size, half_clamp_count)