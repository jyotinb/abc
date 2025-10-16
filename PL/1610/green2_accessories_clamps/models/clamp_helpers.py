# green2_accessories_clamps/models/clamp_helpers.py
# HELPER FUNCTIONS - Data retrieval, accumulator operations, utility methods

import logging
_logger = logging.getLogger(__name__)

# =============================================
# ACCUMULATOR HELPER METHODS
# =============================================

def add_to_clamp_accumulator(accumulator, clamp_type, size, quantity):
    """Add clamps to accumulator (combines same type and size)"""
    if quantity <= 0:
        return
    key = (clamp_type, size)
    accumulator[key] = accumulator.get(key, 0) + quantity

def add_to_clamp_accumulator_separate(accumulator, component_name, size, quantity):
    """Add clamps without combining (for special components like purlin clamps)"""
    if quantity <= 0:
        return
    key = (component_name, size)
    accumulator[key] = accumulator.get(key, 0) + quantity

# =============================================
# DATA RETRIEVAL METHODS - TRUSS COMPONENTS
# =============================================

def get_bottom_chord_data(record):
    """Get bottom chord data from truss components"""
    bottom_chord = record.truss_component_ids.filtered(
        lambda c: 'Bottom Chord' in c.name and 'Female' not in c.name and 
        'V Support' not in c.name
    )
    data = {'count': 0, 'size': None}
    if bottom_chord:
        data['count'] = sum(bottom_chord.mapped('nos'))
        for component in bottom_chord:
            if component.pipe_id and component.pipe_id.pipe_size:
                data['size'] = f"{component.pipe_id.pipe_size.size_in_mm:.0f}mm"
                break
    return data

def get_v_support_count(record):
    """Get V support count from truss components - Works with merged V Support"""
    # Get the single merged V Support component
    v_support = record.truss_component_ids.filtered(
        lambda c: c.name == 'V Support Bottom Chord'
    )
    
    if v_support:
        return v_support.nos
    
    # Fallback: Try old separate components for backward compatibility
    v_support_normal = record.truss_component_ids.filtered(
        lambda c: c.name == 'V Support Bottom Chord' and '(AF)' not in c.name
    )
    v_support_af = record.truss_component_ids.filtered(
        lambda c: c.name == 'V Support Bottom Chord (AF)'
    )
    
    total = 0
    if v_support_normal:
        total += v_support_normal.nos
    if v_support_af:
        total += v_support_af.nos
    
    return total

def get_big_arch_data(record):
    """Get big arch data from truss components"""
    big_arch = record.truss_component_ids.filtered(lambda c: c.name == 'Big Arch')
    data = {'count': 0, 'size': None}
    if big_arch:
        data['count'] = big_arch.nos
        if big_arch.pipe_id and big_arch.pipe_id.pipe_size:
            data['size'] = f"{big_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return data

def get_small_arch_data(record):
    """Get small arch data from truss components"""
    small_arch = record.truss_component_ids.filtered(lambda c: c.name == 'Small Arch')
    data = {'count': 0, 'size': None}
    if small_arch:
        data['count'] = small_arch.nos
        if small_arch.pipe_id and small_arch.pipe_id.pipe_size:
            data['size'] = f"{small_arch.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return data

def get_vent_big_support_count(record):
    """Get vent support count for big arch"""
    vent_support = record.truss_component_ids.filtered(
        lambda c: c.name == 'Vent Support for Big Arch')
    return vent_support.nos if vent_support else 0

def get_small_arch_support_count(record):
    """Get total small arch support count"""
    total = 0
    small_big = record.truss_component_ids.filtered(
        lambda c: c.name == 'Arch Support Small for Big Arch')
    small_small = record.truss_component_ids.filtered(
        lambda c: c.name == 'Arch Support Small for Small Arch')
    if small_big:
        total += small_big.nos
    if small_small:
        total += small_small.nos
    return total

def get_big_arch_support_count(record):
    """Get total big arch support count"""
    total = 0
    big_big = record.truss_component_ids.filtered(
        lambda c: c.name == 'Arch Support Big (Big Arch)')
    big_small = record.truss_component_ids.filtered(
        lambda c: c.name == 'Arch Support Big (Small Arch)')
    if big_big:
        total += big_big.nos
    if big_small:
        total += big_small.nos
    return total

def get_arch_support_straight_middle_data(record):
    """Get arch support straight middle data"""
    arch_support = record.truss_component_ids.filtered(
        lambda c: c.name == 'Arch Support Straight Middle')
    data = {'count': 0, 'size': None}
    if arch_support:
        data['count'] = arch_support.nos
        if arch_support.pipe_id and arch_support.pipe_id.pipe_size:
            data['size'] = f"{arch_support.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return data

def get_small_arch_purlin_size(record):
    """Get Small Arch Purlin pipe size from truss components"""
    small_arch_purlin = record.truss_component_ids.filtered(
        lambda c: 'Small Arch Purlin' in c.name or 'Small Purlin' in c.name)
    if small_arch_purlin and small_arch_purlin.pipe_id and small_arch_purlin.pipe_id.pipe_size:
        return f"{small_arch_purlin.pipe_id.pipe_size.size_in_mm:.0f}mm"
    
    # Fallback to Small Arch size if purlin not found
    small_arch_data = get_small_arch_data(record)
    return small_arch_data['size']

# =============================================
# DATA RETRIEVAL METHODS - FRAME COMPONENTS
# =============================================

def get_middle_column_data(record):
    """Get middle column data from frame components"""
    middle_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'Middle Columns')
    data = {'count': 0, 'size': None}
    if middle_columns:
        data['count'] = middle_columns.nos
        if middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
            data['size'] = f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return data

def get_main_column_pipe_size(record):
    """Get Main Column pipe size"""
    main_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'Main Columns')
    if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
        return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    
    # Fallback to AF Main Columns if Main Columns not found
    af_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'AF Main Columns')
    if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
        return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    
    return None

def get_thick_column_pipe_size(record):
    """Get Thick Column pipe size"""
    thick_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'Thick Columns')
    if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
        return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return None

def get_af_column_pipe_size(record):
    """Get AF Column pipe size (Anchor Frame columns)"""
    af_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'AF Main Columns')
    if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
        return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return None

def get_af_support_column_pipe_size(record):
    """Get pipe size for AF support columns (priority: AF Main → Thick → Main)
    NOTE: This is used for V Support calculations, NOT for middle columns in ASC
    """
    # First check for AF Main Columns
    af_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'AF Main Columns')
    if af_columns and af_columns.pipe_id and af_columns.pipe_id.pipe_size:
        return f"{af_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    
    # Then check Thick Columns
    thick_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'Thick Columns')
    if thick_columns and thick_columns.pipe_id and thick_columns.pipe_id.pipe_size:
        return f"{thick_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    
    # Finally check Main Columns
    main_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'Main Columns')
    if main_columns and main_columns.pipe_id and main_columns.pipe_id.pipe_size:
        return f"{main_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    
    return None

def get_middle_column_pipe_size(record):
    """Get Middle Column pipe size"""
    middle_columns = record.frame_component_ids.filtered(
        lambda c: c.name == 'Middle Columns')
    if middle_columns and middle_columns.pipe_id and middle_columns.pipe_id.pipe_size:
        return f"{middle_columns.pipe_id.pipe_size.size_in_mm:.0f}mm"
    return None

def get_actual_column_counts(record):
    """Get actual column counts from frame_component_ids"""
    counts = {
        'main': 0,
        'af_main': 0,
        'thick': 0,
        'middle': 0,
        'quadruple': 0
    }
    
    if not hasattr(record, 'frame_component_ids'):
        return counts
    
    for component in record.frame_component_ids:
        if component.name == 'Main Columns':
            counts['main'] = component.nos
        elif component.name == 'AF Main Columns':
            counts['af_main'] = component.nos
        elif component.name == 'Thick Columns':
            counts['thick'] = component.nos
        elif component.name == 'Middle Columns':
            counts['middle'] = component.nos
        elif component.name == 'Quadruple Columns':
            counts['quadruple'] = component.nos
    
    return counts

# =============================================
# DATA RETRIEVAL METHODS - ASC COMPONENTS
# =============================================

def get_asc_pipe_size(record):
    """Get ASC pipe size from ASC components"""
    if hasattr(record, 'asc_component_ids'):
        asc_pipes = record.asc_component_ids.filtered(
            lambda c: 'ASC Pipes' in c.name)
        if asc_pipes and asc_pipes[0].pipe_id and asc_pipes[0].pipe_id.pipe_size:
            return f"{asc_pipes[0].pipe_id.pipe_size.size_in_mm:.0f}mm"
    return None

# =============================================
# V SUPPORT DISTRIBUTION CALCULATIONS - FIXED
# =============================================

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
            half_af = no_anchor_frame_lines * (no_of_spans - 1)
            half_main = ((no_of_spans - 1) * (no_of_bays + 1)) - half_af
            full_thick = 2 * (no_of_bays + 1)
            
            distribution['af']['half'] = half_af
            distribution['main']['half'] = half_main
            distribution['thick']['full'] = full_thick
    
    # Calculate total counts for each column type
    for col_type in distribution:
        distribution[col_type]['count'] = (
            distribution[col_type].get('full', 0) + 
            distribution[col_type].get('half', 0)
        )
    
    return distribution

# =============================================
# DETAIL CONVERSION METHODS
# =============================================

def convert_accumulator_to_details(record, accumulator, category, start_sequence):
    """Convert accumulator data to detail format for wizard"""
    details = []
    seq = start_sequence
    for (clamp_identifier, size), quantity in accumulator.items():
        if '(' in clamp_identifier:
            clamp_type = clamp_identifier.split('(')[0].strip()
        else:
            clamp_type = clamp_identifier
        
        details.append({
            'sequence': seq,
            'category': category,
            'component': clamp_identifier,
            'clamp_type': clamp_type,
            'size': size,
            'quantity': quantity,
            'formula': f"Calculated from {category.lower()}",
            'unit_price': get_clamp_price(record, clamp_type, size),
        })
        seq += 10
    return details

def get_clamp_price(record, clamp_type, size):
    """Get clamp price from master data"""
    master_record = record.env['accessories.master'].search([
        ('name', '=', clamp_type),
        ('category', '=', 'clamps'),
        ('size_specification', '=', size),
        ('active', '=', True)
    ], limit=1)
    return master_record.unit_price if master_record else 0.0