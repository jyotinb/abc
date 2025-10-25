"""
V Support Main Column Clamp Calculations
"""
import logging
from .. import clamp_helpers as helpers

_logger = logging.getLogger(__name__)


def accumulate_v_support_main_column_clamps(record, accumulator):
    """Accumulate V Support clamps with Full/Half split"""
    v_support_count = helpers.get_v_support_count(record)
    if v_support_count == 0:
        return
    
    thick_column = getattr(record, 'thick_column', '0')
    no_anchor_frame_lines = getattr(record, 'no_anchor_frame_lines', 0)
    v_support_per_frame = int(getattr(record, 'v_support_bottom_chord_frame', 0))
    v_support_frames = v_support_count // v_support_per_frame if v_support_per_frame > 0 else 0
    v_support_for_af = getattr(record, 'v_support_for_af', True)  # Get from record
    
    if v_support_frames == 0:
        _logger.warning("V Support count exists but v_support_bottom_chord_frame is 0")
        return
    
    _logger.info(f"=== V SUPPORT MAIN COLUMN CLAMPS ===")
    _logger.info(f"V Support count: {v_support_count}, Frames: {v_support_frames}")
    _logger.info(f"Thick Column: {thick_column}, AF Lines: {no_anchor_frame_lines}")
    _logger.info(f"V Support for AF Lines: {v_support_for_af}")
    
    column_counts = helpers.get_actual_column_counts(record)
    
    v_support_distribution = calculate_v_support_column_distribution(
        record, v_support_count, v_support_frames, thick_column, no_anchor_frame_lines, 
        column_counts
    )
    
    for column_type, data in v_support_distribution.items():
        if data['count'] == 0 or not data['size']:
            continue
        
        column_label = column_type.upper()
        has_split = 'full' in data and 'half' in data
        
        if has_split:
            if data['full'] > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', data['size'], data['full'])
                _logger.info(f"  {data['full']} × Full Clamp - {data['size']} ({column_label})")
            
            if data['half'] > 0:
                helpers.add_to_clamp_accumulator(accumulator, 'Half Clamp', data['size'], data['half'])
                _logger.info(f"  {data['half']} × Half Clamp - {data['size']} ({column_label})")
        else:
            helpers.add_to_clamp_accumulator(accumulator, 'Full Clamp', data['size'], data['count'])
            _logger.info(f"  {data['count']} × Full Clamp - {data['size']} ({column_label})")


def calculate_v_support_column_distribution(record, v_support_count, v_support_frames, 
                                            thick_column, no_anchor_frame_lines, column_counts):
    """
    Calculate V Support clamp distribution based on thick column configuration
    
    Returns dictionary with structure:
    {
        'main': {'count': X, 'size': 'Y', 'full': A, 'half': B},
        'af': {'count': X, 'size': 'Y', 'full': A, 'half': B},
        'thick': {'count': X, 'size': 'Y', 'full': A, 'half': B}
    }
    """
    from .. import clamp_helpers as helpers
    
    no_of_spans = getattr(record, 'no_of_spans', 0)
    no_of_bays = getattr(record, 'no_of_bays', 0)
    v_support_for_af = getattr(record, 'v_support_for_af', True)  # Get from record
    
    # Get column sizes using helper functions
    main_size = helpers.get_main_column_pipe_size(record)
    af_size = helpers.get_af_support_column_pipe_size(record)
    thick_size = helpers.get_thick_column_pipe_size(record)
    
    distribution = {
        'main': {'count': 0, 'size': main_size, 'full': 0, 'half': 0},
        'af': {'count': 0, 'size': af_size, 'full': 0, 'half': 0},
        'thick': {'count': 0, 'size': thick_size, 'full': 0, 'half': 0}
    }
    
    # THICK COLUMN = 0 (None)
    if thick_column == '0':
        if no_anchor_frame_lines == 0:
            # CASE 3A: AF Lines = 0
            distribution['main']['half'] = (no_of_spans - 1) * (no_of_bays + 1)
            distribution['main']['full'] = 2 * (no_of_bays + 1)
        else:
            # CASE 3B: AF Lines > 0
            half_af = no_anchor_frame_lines * (no_of_spans - 1)
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af
            full_af = 2 * no_anchor_frame_lines
            full_main = (2 * (no_of_bays + 1)) - full_af
            
            distribution['af']['half'] = half_af
            distribution['af']['full'] = full_af
            distribution['main']['half'] = half_main
            distribution['main']['full'] = full_main
    
    # THICK COLUMN = 1 (4 Corner)
    elif thick_column == '1':
        if no_anchor_frame_lines == 0:
            # CASE 4A: AF Lines = 0
            distribution['main']['half'] = (no_of_spans - 1) * (no_of_bays + 1)
            distribution['main']['full'] = (2 * (no_of_bays + 1)) - 4
            distribution['thick']['full'] = 4
        elif no_anchor_frame_lines == 1:
            # CASE 4B: AF Lines = 1 (Special case - no Full Clamps for AF)
            half_af = no_anchor_frame_lines * (no_of_spans - 1)
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af
            full_thick = 4
            full_main = (2 * (no_of_bays + 1)) - full_thick
            
            distribution['af']['half'] = half_af
            distribution['main']['half'] = half_main
            distribution['thick']['full'] = full_thick
            distribution['main']['full'] = full_main
        else:  # AF Lines > 1
            # CASE 4B: AF Lines > 1
            half_af = no_anchor_frame_lines * (no_of_spans - 1)
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af
            full_af = (2 * no_anchor_frame_lines) - 4
            full_thick = 4
            full_main = (2 * (no_of_bays + 1)) - full_af - full_thick
            
            distribution['af']['half'] = half_af
            distribution['af']['full'] = full_af
            distribution['main']['half'] = half_main
            distribution['main']['full'] = full_main
            distribution['thick']['full'] = full_thick
    
    # THICK COLUMN = 2 (2 Bay Side)
    elif thick_column == '2':
        if no_anchor_frame_lines == 0:
            # CASE 5A: AF Lines = 0
            distribution['main']['half'] = (no_of_spans - 1) * (no_of_bays + 1)
            distribution['thick']['full'] = 2 * (no_of_bays + 1)
        else:
            # CASE 5B: AF Lines > 0
            half_af = no_anchor_frame_lines * (no_of_spans - 1)
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af
            
            distribution['af']['half'] = half_af
            distribution['main']['half'] = half_main
            distribution['thick']['full'] = 2 * (no_of_bays + 1)
    
    # THICK COLUMN = 4 (All 4 Side)
    elif thick_column == '4':
        if no_anchor_frame_lines < 3:
            # CASE 6A: AF Lines < 3
            half_thick = (no_of_spans - 1) * 2
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_thick
            full_thick = 2 * (no_of_bays + 1)
            
            distribution['thick']['half'] = half_thick
            distribution['main']['half'] = half_main
            distribution['thick']['full'] = full_thick
        else:  # AF Lines > 2
            # CASE 6B: AF Lines > 2
            half_af = (no_anchor_frame_lines - 2) * (no_of_spans - 1)
            half_thick = (no_of_spans - 1) * 2
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af - half_thick
            full_thick = 2 * (no_of_bays + 1)
            
            distribution['af']['half'] = half_af
            distribution['thick']['half'] = half_thick
            distribution['main']['half'] = half_main
            distribution['thick']['full'] = full_thick
    
    # THICK COLUMN = 3 (2 Span Side)
    elif thick_column == '3':
        if no_anchor_frame_lines == 0:
            # CASE 7A: AF Lines = 0
            half_thick = (no_of_spans - 1) * 2
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_thick
            full_main = (2 * (no_of_bays + 1)) - 4
            full_thick = 4
            
            distribution['thick']['half'] = half_thick
            distribution['main']['half'] = half_main
            distribution['main']['full'] = full_main
            distribution['thick']['full'] = full_thick
        elif no_anchor_frame_lines > 2:
            # CASE 7B: AF Lines > 2
            half_thick = (no_of_spans - 1) * 2
            half_af = (no_anchor_frame_lines - 2) * (no_of_spans - 1)
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af - half_thick
            full_af = (2 * no_anchor_frame_lines) - 4
            full_thick = 4
            full_main = (2 * (no_of_bays + 1)) - full_af - full_thick
            
            distribution['thick']['half'] = half_thick
            distribution['af']['half'] = half_af
            distribution['main']['half'] = half_main
            distribution['af']['full'] = full_af
            distribution['main']['full'] = full_main
            distribution['thick']['full'] = full_thick
        else:  # AF Lines < 3
            # CASE 7C: AF Lines < 3
            half_thick = (no_of_spans - 1) * no_anchor_frame_lines
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_thick
            full_main = (2 * (no_of_bays + 1)) - (2 * no_anchor_frame_lines)
            full_thick = 2 * no_anchor_frame_lines
            
            distribution['thick']['half'] = half_thick
            distribution['main']['half'] = half_main
            distribution['main']['full'] = full_main
            distribution['thick']['full'] = full_thick
    
    # Apply V support for AF Lines = False logic
    if not v_support_for_af:
        # Zero out all AF clamps
        distribution['af']['half'] = 0
        distribution['af']['full'] = 0
        
        # Subtract from THICK clamps based on configuration
        if thick_column == '1':  # 4 Corner
            if no_anchor_frame_lines < 3:
                distribution['thick']['full'] -= 2 * no_anchor_frame_lines
            # else: AF Lines > 2, no reduction (keeps original 4)
        
        elif thick_column == '2':  # 2 Bay Side
            if no_anchor_frame_lines > 0:
                distribution['thick']['full'] -= 2 * no_anchor_frame_lines
        
        elif thick_column == '4':  # All 4 Side
            if no_anchor_frame_lines < 3:
                distribution['thick']['half'] -= (no_of_spans - 1) * no_anchor_frame_lines
                distribution['thick']['full'] -= no_anchor_frame_lines * 2
            # else: AF Lines > 2, no reduction (keeps original values)
        
        elif thick_column == '3':  # 2 Span Side
            if no_anchor_frame_lines > 2:
                # No reduction for AF Lines > 2 (keeps original values)
                pass
            else:  # AF Lines < 3
                distribution['thick']['half'] -= (no_of_spans - 1) * no_anchor_frame_lines
                distribution['thick']['full'] -= 2 * no_anchor_frame_lines
    
    # Calculate total counts for each column type
    for col_type in distribution:
        distribution[col_type]['count'] = (
            distribution[col_type].get('full', 0) + 
            distribution[col_type].get('half', 0)
        )
    
    return distribution