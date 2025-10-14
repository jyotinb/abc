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
    """Get V support count from truss components"""
    v_support = record.truss_component_ids.filtered(lambda c: c.name == 'V Support Bottom Chord')
    return v_support.nos if v_support else 0

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
# V SUPPORT DISTRIBUTION CALCULATIONS
# =============================================

def calculate_v_support_column_distribution(record, total_v_supports, v_support_frames, 
                                           thick_column, af_lines, column_counts):
    """Calculate V Support distribution across column types"""
    distribution = {
        'thick': {'count': 0, 'size': get_thick_column_pipe_size(record)},
        'af': {'count': 0, 'size': get_af_support_column_pipe_size(record)},
        'main': {'count': 0, 'size': get_main_column_pipe_size(record)}
    }
    
    v_supports_per_line = total_v_supports // v_support_frames if v_support_frames > 0 else 0
    
    if v_supports_per_line == 0:
        _logger.warning("V supports per line is 0")
        return distribution
    
    columns_per_frame = record.no_of_spans + 1
    
    if thick_column == '0':  # No thick columns
        _distribute_v_supports_no_thick(
            record, distribution, v_support_frames, v_supports_per_line, 
            af_lines, columns_per_frame, column_counts
        )
    elif thick_column == '1':  # 4 Corners
        _distribute_v_supports_4_corners(
            record, distribution, v_support_frames, v_supports_per_line,
            af_lines, columns_per_frame, column_counts
        )
    elif thick_column == '2':  # 2 Bay Side
        _distribute_v_supports_bay_side(
            record, distribution, v_support_frames, v_supports_per_line,
            af_lines, columns_per_frame, column_counts
        )
    elif thick_column == '3':  # 2 Span Side
        _distribute_v_supports_span_side(
            record, distribution, v_support_frames, v_supports_per_line,
            af_lines, columns_per_frame, column_counts
        )
    elif thick_column == '4':  # All 4 Side
        _distribute_v_supports_all_4_side(
            distribution, v_support_frames, v_supports_per_line,
            columns_per_frame
        )
    
    # Verify totals match
    calculated_total = sum(d['count'] for d in distribution.values())
    if calculated_total != total_v_supports:
        _logger.warning(f"V Support distribution mismatch: calculated {calculated_total}, expected {total_v_supports}")
        difference = total_v_supports - calculated_total
        distribution['main']['count'] += difference
    
    return distribution

def _distribute_v_supports_no_thick(record, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
    """Distribute V Supports when thick_column = '0' (No thick columns)"""
    if af_lines > 0 and col_counts['af_main'] > 0:
        # Some frames have AF columns
        af_frame_ratio = min(af_lines / v_frames, 1.0)
        af_v_supports = int(af_frame_ratio * v_frames * v_per_line)
        
        dist['af']['count'] = af_v_supports
        dist['main']['count'] = (v_frames * v_per_line) - af_v_supports
    else:
        # All frames use main columns
        dist['main']['count'] = v_frames * v_per_line

def _distribute_v_supports_4_corners(record, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
    """Distribute V Supports when thick_column = '1' (4 Corners)"""
    if v_frames >= 2:
        # Thick columns on first and last frames (corners)
        thick_per_end_frame = min(2, v_per_line)
        dist['thick']['count'] = 2 * thick_per_end_frame
        
        remaining = (v_frames * v_per_line) - dist['thick']['count']
        
        if af_lines > 0 and col_counts['af_main'] > 0:
            af_ratio = min(af_lines / v_frames, 0.5)
            dist['af']['count'] = int(af_ratio * remaining)
            dist['main']['count'] = remaining - dist['af']['count']
        else:
            dist['main']['count'] = remaining
    else:
        # Only one frame, use thick columns for corners
        dist['thick']['count'] = min(2, v_per_line)
        dist['main']['count'] = v_per_line - dist['thick']['count']

def _distribute_v_supports_bay_side(record, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
    """Distribute V Supports when thick_column = '2' (Both Bay Side)"""
    # Thick columns on all frames, but only for bay side positions
    thick_per_frame = min(2, v_per_line)  # 2 per frame for bay sides
    dist['thick']['count'] = v_frames * thick_per_frame
    
    remaining = (v_frames * v_per_line) - dist['thick']['count']
    
    if af_lines > 0 and col_counts['af_main'] > 0:
        af_ratio = min(af_lines / v_frames, 0.3)
        dist['af']['count'] = int(af_ratio * remaining)
        dist['main']['count'] = remaining - dist['af']['count']
    else:
        dist['main']['count'] = remaining

def _distribute_v_supports_span_side(record, dist, v_frames, v_per_line, af_lines, cols_per_frame, col_counts):
    """Distribute V Supports when thick_column = '3' (Both Span Side)"""
    # Thick columns on span side frames (front and back)
    total_bays = record.no_of_bays + 1
    span_side_frames = 2  # Front and back frames
    
    if v_frames <= span_side_frames:
        # All frames are span side
        dist['thick']['count'] = v_frames * v_per_line
    else:
        # Calculate how many V supports go to span side frames
        span_ratio = span_side_frames / total_bays
        thick_v_supports = int(span_ratio * v_frames * v_per_line)
        dist['thick']['count'] = thick_v_supports
        
        remaining = (v_frames * v_per_line) - thick_v_supports
        if af_lines > 0 and col_counts['af_main'] > 0:
            af_ratio = min(af_lines / v_frames, 0.3)
            dist['af']['count'] = int(af_ratio * remaining)
            dist['main']['count'] = remaining - dist['af']['count']
        else:
            dist['main']['count'] = remaining

def _distribute_v_supports_all_4_side(dist, v_frames, v_per_line, cols_per_frame):
    """Distribute V Supports when thick_column = '4' (All 4 Side)"""
    # All columns are thick columns
    dist['thick']['count'] = v_frames * v_per_line

# =============================================
# DETAIL CONVERSION METHODS
# =============================================

def convert_accumulator_to_details(record, accumulator, category, start_sequence):
    """Convert accumulator data to detail format for wizard"""
    details = []
    seq = start_sequence
    for (clamp_identifier, size), quantity in accumulator.items():
        # Extract base clamp type from identifier
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