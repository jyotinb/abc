# green2_accessories_clamps/models/clamp_calculations_standard.py
# STANDARD CLAMP CALCULATIONS - W Type, M Type, Arch Support, Purlin, V Support

import logging
from . import clamp_helpers as helpers

_logger = logging.getLogger(__name__)

# =============================================
# W TYPE CLAMPS
# =============================================

def accumulate_w_type_clamps(record, accumulator):
    """Accumulate W Type clamps"""
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    v_support_count = helpers.get_v_support_count(record)
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    vent_big_support_count = helpers.get_vent_big_support_count(record)
    arch_support_straight_middle_data = helpers.get_arch_support_straight_middle_data(record)
    middle_column_data = helpers.get_middle_column_data(record)
    
    _logger.info("=== W TYPE CLAMPS ===")
    
    if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
        qty = (bottom_chord_data['count'] * 3) + v_support_count
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
    
    if big_arch_data['count'] > 0 and big_arch_data['size']:
        qty = (big_arch_data['count'] * 2) + vent_big_support_count
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', big_arch_data['size'], qty)
        _logger.info(f"  {qty} × Full Clamp - {big_arch_data['size']} (Big Arch)")
    
    if small_arch_data['count'] > 0 and small_arch_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', small_arch_data['size'], 
                                      small_arch_data['count'])
        _logger.info(f"  {small_arch_data['count']} × Full Clamp - {small_arch_data['size']} (Small Arch)")
    
    if arch_support_straight_middle_data['count'] > 0 and arch_support_straight_middle_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', 
                                      arch_support_straight_middle_data['size'], 
                                      arch_support_straight_middle_data['count'])
        helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', 
                                      arch_support_straight_middle_data['size'], 
                                      arch_support_straight_middle_data['count'])
        _logger.info(f"  {arch_support_straight_middle_data['count']} × Full Clamp - "
                    f"{arch_support_straight_middle_data['size']} (Arch Support Straight Middle)")
        _logger.info(f"  {arch_support_straight_middle_data['count']} × Half Clamp - "
                    f"{arch_support_straight_middle_data['size']} (Arch Support Straight Middle)")
    
    if middle_column_data['count'] > 0 and middle_column_data['size']:
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', middle_column_data['size'], 
                                      middle_column_data['count'])
        helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', middle_column_data['size'], 
                                      middle_column_data['count'])
        _logger.info(f"  {middle_column_data['count']} × Full Clamp - {middle_column_data['size']} (Middle Column)")
        _logger.info(f"  {middle_column_data['count']} × Half Clamp - {middle_column_data['size']} (Middle Column)")

# =============================================
# M TYPE CLAMPS
# =============================================

def accumulate_m_type_clamps(record, accumulator):
    """Accumulate M Type clamps"""
    bottom_chord_data = helpers.get_bottom_chord_data(record)
    v_support_count = helpers.get_v_support_count(record)
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    vent_big_support_count = helpers.get_vent_big_support_count(record)
    middle_column_data = helpers.get_middle_column_data(record)
    
    _logger.info(f"=== M TYPE CLAMPS (Bottom Chord Type: {record.bottom_chord_clamp_type}) ===")
    
    if bottom_chord_data['count'] > 0 and bottom_chord_data['size']:
        if record.bottom_chord_clamp_type == 'single':
            qty = (bottom_chord_data['count'] * 3) + v_support_count
        else:  # triple
            qty = (bottom_chord_data['count'] * 5) + v_support_count
        helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', bottom_chord_data['size'], qty)
        _logger.info(f"  {qty} × Full Clamp - {bottom_chord_data['size']} (Bottom Chord)")
    
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

# =============================================
# ARCH SUPPORT CLAMPS
# =============================================

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

# =============================================
# PURLIN CLAMPS
# =============================================

def accumulate_purlin_clamps(record, accumulator):
    """Accumulate purlin clamps"""
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    
    _logger.info("=== PURLIN CLAMPS ===")
    
    # Big Arch Purlin Clamps
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
    
    # Small Arch Purlin Clamps
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



# green2_accessories_clamps/models/clamp_calculations_standard.py
# ADD THIS TO THE EXISTING FILE - After the existing purlin_clamps function

def accumulate_arch_middle_purlin_clamps(record, accumulator):
    """
    Accumulate Arch Middle Purlin clamps for both Big and Small Arch
    Based on the configuration selection (4 Corner, Front & Back, Both Side, 4 Side, All)
    """
    _logger.info("=== ARCH MIDDLE PURLIN CLAMPS ===")
    
    # Get Big and Small Arch sizes
    big_arch_data = helpers.get_big_arch_data(record)
    small_arch_data = helpers.get_small_arch_data(record)
    
    # Get configuration values
    arch_middle_purlin_big_arch = getattr(record, 'arch_middle_purlin_big_arch', '0')
    arch_middle_purlin_big_arch_pcs = int(getattr(record, 'arch_middle_purlin_big_arch_pcs', 0))
    arch_middle_purlin_small_arch = getattr(record, 'arch_middle_purlin_small_arch', '0')
    arch_middle_purlin_small_arch_pcs = int(getattr(record, 'arch_middle_purlin_small_arch_pcs', 0))
    
    # Get component counts for validation
    big_arch_purlin_count = _get_arch_middle_purlin_count(record, 'big')
    small_arch_purlin_count = _get_arch_middle_purlin_count(record, 'small')
    
    # BIG ARCH MIDDLE PURLIN CLAMPS
    if arch_middle_purlin_big_arch != '0' and big_arch_data['size'] and big_arch_purlin_count > 0:
        _logger.info(f"Processing Big Arch Middle Purlin - Config: {arch_middle_purlin_big_arch}, Pcs: {arch_middle_purlin_big_arch_pcs}")
        _calculate_arch_middle_purlin_clamps_for_type(
            record, accumulator, 
            'big', 
            big_arch_data['size'], 
            arch_middle_purlin_big_arch, 
            arch_middle_purlin_big_arch_pcs,
            big_arch_purlin_count
        )
    
    # SMALL ARCH MIDDLE PURLIN CLAMPS
    if arch_middle_purlin_small_arch != '0' and small_arch_data['size'] and small_arch_purlin_count > 0:
        _logger.info(f"Processing Small Arch Middle Purlin - Config: {arch_middle_purlin_small_arch}, Pcs: {arch_middle_purlin_small_arch_pcs}")
        _calculate_arch_middle_purlin_clamps_for_type(
            record, accumulator, 
            'small', 
            small_arch_data['size'], 
            arch_middle_purlin_small_arch, 
            arch_middle_purlin_small_arch_pcs,
            small_arch_purlin_count
        )

def _get_arch_middle_purlin_count(record, arch_type):
    """Get the count of Arch Middle Purlin components from truss_component_ids"""
    if arch_type == 'big':
        component_name = 'Arch Middle Purlin Big Arch'
    else:
        component_name = 'Arch Middle Purlin Small Arch'
    
    purlin_component = record.truss_component_ids.filtered(
        lambda c: c.name == component_name
    )
    return purlin_component.nos if purlin_component else 0

def _calculate_arch_middle_purlin_clamps_for_type(record, accumulator, arch_type, arch_size, 
                                                   config_type, pcs_count, total_purlin_count):
    """
    Calculate clamps for a specific arch middle purlin type (big or small)
    
    config_type values:
    '0': None
    '1': 4 Corners
    '2': Front & Back
    '3': Both Sides
    '4': 4 Sides
    '5': All
    """
    arch_label = "Big Arch" if arch_type == 'big' else "Small Arch"
    
    full_clamp_count = 0
    half_clamp_count = 0
    
    if config_type == '1':  # 4 Corners
        # Full Clamps = No of Arch Middle Purlin * 2
        full_clamp_count = total_purlin_count * 2
        _logger.info(f"  {arch_label} (4 Corners): Full = {full_clamp_count}")
        
    elif config_type == '2':  # Front & Back
        # Full Clamps = No of Arch Middle Purlin * 2
        full_clamp_count = total_purlin_count * 2
        _logger.info(f"  {arch_label} (Front & Back): Full = {full_clamp_count}")
        
    elif config_type == '3':  # Both Sides
        # Full Clamps = 4 * Pcs
        full_clamp_count = 4 * pcs_count
        # Half Clamps = (No of Arch Middle Purlin * 2) - (4 * Pcs)
        half_clamp_count = (total_purlin_count * 2) - (4 * pcs_count)
        _logger.info(f"  {arch_label} (Both Sides): Full = {full_clamp_count}, Half = {half_clamp_count}")
        
    elif config_type == '4':  # 4 Sides
        # Full Clamps = ((((No of Spans - 2) * 4) + 4) * Pcs)
        no_of_spans = record.no_of_spans
        full_clamp_count = ((((no_of_spans - 2) * 4) + 4) * pcs_count)
        # Half Clamps = Total Purlin Count - (Full Clamps / 2)
        half_clamp_count = total_purlin_count - (full_clamp_count // 2)
        _logger.info(f"  {arch_label} (4 Sides): Full = {full_clamp_count}, Half = {half_clamp_count}")
        
    elif config_type == '5':  # All
        # Full Clamps = No of Spans * 2
        full_clamp_count = record.no_of_spans * 2
        # Half Clamps = No of Spans * (No of Bays - 1)
        half_clamp_count = record.no_of_spans * (record.no_of_bays - 1)
        _logger.info(f"  {arch_label} (All): Full = {full_clamp_count}, Half = {half_clamp_count}")
    
    # Add clamps to accumulator with descriptive names
    if full_clamp_count > 0:
        component_name = f"Full Clamp (Arch Middle Purlin {arch_label})"
        helpers.add_to_clamp_accumulator_separate(
            accumulator, component_name, arch_size, full_clamp_count
        )
    
    if half_clamp_count > 0:
        component_name = f"Half Clamp (Arch Middle Purlin {arch_label})"
        helpers.add_to_clamp_accumulator_separate(
            accumulator, component_name, arch_size, half_clamp_count
        )


# UPDATE THE MAIN FUNCTION in green_master_clamps.py to call this:
# In the _calculate_advanced_clamps method, after the existing purlin clamps:
# std_calc.accumulate_arch_middle_purlin_clamps(self, clamp_accumulator)


# =============================================
# V SUPPORT CLAMPS
# =============================================

def accumulate_v_support_main_column_clamps(record, accumulator):
    """Accumulate V Support clamps"""
    v_support_count = helpers.get_v_support_count(record)
    if v_support_count == 0:
        return
    
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = getattr(record, 'no_anchor_frame_lines', 0)
    v_support_frames = int(getattr(record, 'v_support_bottom_chord_frame', 0))
    
    if v_support_frames == 0:
        _logger.warning("V Support count exists but v_support_bottom_chord_frame is 0")
        return
    
    _logger.info(f"=== V SUPPORT MAIN COLUMN CLAMPS ===")
    _logger.info(f"V Support count: {v_support_count}, Frames: {v_support_frames}")
    _logger.info(f"Thick Column: {thick_column}, AF Lines: {no_anchor_frame_lines}")
    
    column_counts = helpers.get_actual_column_counts(record)
    
    v_support_distribution = helpers.calculate_v_support_column_distribution(
        record,
        v_support_count,
        v_support_frames,
        thick_column,
        no_anchor_frame_lines,
        column_counts
    )
    
    for column_type, data in v_support_distribution.items():
        if data['count'] > 0 and data['size']:
            helpers.add_to_clamp_accumulator(
                accumulator, 
                'Full Clamp', 
                data['size'], 
                data['count']
            )
            _logger.info(f"  {data['count']} × Full Clamp - {data['size']} ({column_type})")