from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from math import ceil, sqrt, floor
import logging

_logger = logging.getLogger(__name__)

class LengthMaster(models.Model):
    _name = 'length.master'
    _description = 'Length Master for Component Configuration'
    _order = 'length_value asc'
    
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    length_value = fields.Float(string='Length Value', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    available_for_fields = fields.Many2many(
        'length.field.option',
        'length_master_field_option_rel',
        'length_id',
        'field_option_id',
        string='Available For Fields',
        help="Select which Length Master fields this length should be available for",
        tracking=True
    )
    
    
    length_category = fields.Selection([
        ('small', 'Small (< 1m)'),
        ('medium', 'Medium (1-3m)'),
        ('large', 'Large (> 3m)'),
    ], string='Length Category', compute='_compute_length_category', store=True)
    
    @api.depends('length_value')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.length_value}m" if record.length_value else "0.0m"
    
    @api.depends('length_value')
    def _compute_length_category(self):
        for record in self:
            if not record.length_value:
                record.length_category = 'small'
            elif record.length_value < 1.0:
                record.length_category = 'small'
            elif record.length_value <= 3.0:
                record.length_category = 'medium'
            else:
                record.length_category = 'large'
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.length_value}m" if record.length_value else "0.0m"
            result.append((record.id, name))
        return result

class LengthFieldOption(models.Model):
    _name = 'length.field.option'
    _description = 'Length Field Options'
    _order = 'display_name'
    
    name = fields.Char(string='Field Name', required=True, tracking=True)
    display_name = fields.Char(string='Display Name', required=True, tracking=True)
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

class ComponentLine(models.Model):
    _name = 'component.line'
    _description = 'Component Line with Excel-style functionality'
    _order = 'section, sequence, name'
    
    green_master_id = fields.Many2one('green.master', string='Green Master', ondelete='cascade', required=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    section = fields.Selection([
        ('frame', 'Frame Components'), 
        ('truss', 'Truss Components'),
        ('side_screen', 'Side Screen Components'),
        ('lower', 'Lower Section Components'),
        ('asc', 'ASC Components'),
    ], string='Section', required=True, tracking=True)
    
    name = fields.Char(string='Component Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    required = fields.Boolean(string='Required', default=True, tracking=True)
    
    nos = fields.Integer(string='Nos', default=0, tracking=True)
    length = fields.Float(string='Length (m)', default=0.0, tracking=True)
    
    use_length_master = fields.Boolean(string='Use Length Master', default=False, tracking=True)
    length_master_id = fields.Many2one('length.master', string='Select Length', tracking=True)
    custom_length = fields.Float(string='Custom Length', default=0.0, tracking=True)
    
    pipe_id = fields.Many2one('pipe.management', string='Pipe Specification', tracking=True)
    
    pipe_type = fields.Char(string='Pipe Type', compute='_compute_pipe_details', store=True)
    pipe_size = fields.Float(string='Size (mm)', compute='_compute_pipe_details', store=True)
    wall_thickness = fields.Float(string='WT (mm)', compute='_compute_pipe_details', store=True)
    weight_per_unit = fields.Float(string='Weight/Unit (kg/m)', compute='_compute_pipe_details', store=True)
    rate_per_kg = fields.Float(string='Rate/Kg', compute='_compute_pipe_details', store=True)
    
    total_length = fields.Float(string='Total Length (m)', compute='_compute_totals', store=True)
    total_weight = fields.Float(string='Total Weight (kg)', compute='_compute_totals', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_totals', store=True)
    
    is_calculated = fields.Boolean(string='Auto Calculated', default=False, tracking=True)
    notes = fields.Text(string='Notes', tracking=True)
    
    @api.depends('pipe_id')
    def _compute_pipe_details(self):
        for record in self:
            if record.pipe_id:
                try:
                    record.pipe_type = record.pipe_id.name.name if record.pipe_id.name else ''
                    record.pipe_size = record.pipe_id.pipe_size.size_in_mm if record.pipe_id.pipe_size else 0.0
                    record.wall_thickness = record.pipe_id.wall_thickness.thickness_in_mm if record.pipe_id.wall_thickness else 0.0
                    record.weight_per_unit = record.pipe_id.weight or 0.0
                    record.rate_per_kg = record.pipe_id.rate or 0.0
                except Exception:
                    record.pipe_type = ''
                    record.pipe_size = 0.0
                    record.wall_thickness = 0.0
                    record.weight_per_unit = 0.0
                    record.rate_per_kg = 0.0
            else:
                record.pipe_type = ''
                record.pipe_size = 0.0
                record.wall_thickness = 0.0
                record.weight_per_unit = 0.0
                record.rate_per_kg = 0.0
    
    @api.depends('nos', 'length', 'weight_per_unit', 'rate_per_kg')
    def _compute_totals(self):
        for record in self:
            record.total_length = record.nos * record.length
            record.total_weight = record.total_length * (record.weight_per_unit or 0)
            record.total_cost = record.total_weight * (record.rate_per_kg or 0)
    
    @api.onchange('use_length_master', 'length_master_id', 'custom_length')
    def _onchange_length_configuration(self):
        if self._context.get('from_ui', True):
            if self.use_length_master and self.length_master_id:
                self.length = self.length_master_id.length_value
            elif not self.use_length_master and self.custom_length > 0:
                self.length = self.custom_length
     
    def write(self, vals):
        length_states = {}
        for record in self:
            length_states[record.id] = {
                'length': record.length,
                'use_length_master': record.use_length_master,
                'custom_length': record.custom_length
            }
        
        result = super().write(vals)
        
        for record in self:
            if record.id in length_states:
                state = length_states[record.id]
                if not record.use_length_master and record.custom_length > 0:
                    if record.length != record.custom_length:
                        super(ComponentLine, record).write({'length': record.custom_length})
                elif record.use_length_master and record.length_master_id:
                    expected_length = record.length_master_id.length_value
                    if record.length != expected_length:
                        super(ComponentLine, record).write({'length': expected_length})
        
        return result
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.section:
                try:
                    section_name = dict(record._fields['section'].selection)[record.section]
                    name = f"[{section_name}] {name}"
                except (KeyError, AttributeError):
                    pass
            result.append((record.id, name))
        return result

class GreenMaster(models.Model):
    _name = 'green.master'
    _description = 'Greenhouse Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Customer Information
    customer = fields.Char('Customer', size=50, tracking=True)
    address = fields.Char('Address', size=200, tracking=True)
    city = fields.Char('City', size=50, tracking=True)
    mobile = fields.Char('Mobile', size=13, tracking=True)
    email = fields.Char('Email', size=40, tracking=True)
    reference = fields.Char('Reference', size=300, tracking=True)
    is_side_coridoors = fields.Boolean('Is ASC', default=False, tracking=True)
    # Basic Structure Configuration
    structure_type = fields.Selection([
        ('NVPH', 'NVPH'),
        ('NVPH2', 'NVPH2'),
    ], string='Structure Type', required=True, default='NVPH', tracking=True)
    plot_size = fields.Char('Plot Size', size=20, tracking=True)
    total_span_length = fields.Float('Total Span Length', tracking=True)
    total_bay_length = fields.Float('Total Bay Length', tracking=True)
    span_length = fields.Float('Span Length', compute='_compute_calculated_dimensions', store=True)
    bay_length = fields.Float('Bay Length', compute='_compute_calculated_dimensions', store=True)
    structure_size = fields.Float('Structure Size', compute='_compute_calculated_dimensions', store=True)
    gutter_length = fields.Float('Gutter Length', compute='_compute_calculated_dimensions', store=True)
    span_width = fields.Float('Span Width', default=0.00, tracking=True)
    bay_width = fields.Float('Bay Width', default=0.00, tracking=True)
    no_of_bays = fields.Integer('Number of Bays', compute='_compute_calculated_dimensions', store=True)
    no_of_spans = fields.Integer('Number of Spans', compute='_compute_calculated_dimensions', store=True)
    gutter_slope = fields.Selection([
        ('1', '1'),('2', '2')],string = 'Gutter Slope', default='1', tracking=True)
    last_span_gutter = fields.Boolean('Last Span Gutter', default=False, tracking=True)
    top_ridge_height = fields.Float('Top Ridge Height', default=0.00, tracking=True)
    column_height = fields.Float('Column Height', default=0.00, tracking=True)
    bottom_height = fields.Float('Bottom Height', compute='_compute_calculated_dimensions', store=True)
    arch_height = fields.Float('Arch Height', compute='_compute_calculated_dimensions', store=True)
    big_arch_length = fields.Float('Big Arch Length', default=0.00, tracking=True)
    small_arch_length = fields.Float('Small Arch Length', default=0.00, tracking=True)
    foundation_length = fields.Float('Foundation Length', default=0.00, tracking=True)
    last_span_gutter_length = fields.Integer('Last Span Gutter Length', default=0, tracking=True)
    
    # Field needed by multiple modules, so in base
    no_column_big_frame = fields.Selection([
        ('0', '0'),('1', '1'),('2', '2'),('3', '3')
    ], string='No of Big Column per Anchor Frame', required=True, default='0', tracking=True)
    
    # Component Collections
    frame_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'frame')], 
                                         string='Frame Components')
    truss_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'truss')], 
                                         string='Truss Components')
    side_screen_component_ids = fields.One2many('component.line', 'green_master_id',
                                               domain=[('section', '=', 'side_screen')], 
                                               string='Side Screen Components')
    lower_component_ids = fields.One2many('component.line', 'green_master_id', 
                                         domain=[('section', '=', 'lower')], 
                                         string='Lower Section Components')
    asc_component_ids = fields.One2many('component.line', 'green_master_id', 
                                       domain=[('section', '=', 'asc')], 
                                       string='ASC Components')
    
    # Cost Fields
    total_frame_cost = fields.Float('Total Frame Cost', compute='_compute_section_totals', store=True, tracking=True)
    total_truss_cost = fields.Float('Total Truss Cost', compute='_compute_section_totals', store=True, tracking=True)
    total_side_screen_cost = fields.Float('Total Side Screen Cost', compute='_compute_section_totals', store=True, tracking=True)
    total_lower_cost = fields.Float('Total Lower Cost', compute='_compute_section_totals', store=True, tracking=True)
    total_asc_cost = fields.Float('Total ASC Cost', compute='_compute_section_totals', store=True, tracking=True)
    grand_total_cost = fields.Float('Grand Total Cost', compute='_compute_section_totals', store=True, tracking=True)
    
    @api.depends('total_span_length', 'total_bay_length', 'span_width', 'bay_width', 
                 'column_height', 'top_ridge_height')
    def _compute_calculated_dimensions(self):
        """Basic dimension calculations - can be extended by other modules"""
        for record in self:
            record.span_length = record.total_span_length
            record.bay_length = record.total_bay_length
            record.structure_size = record.total_span_length * record.total_bay_length
            record.no_of_bays = int(record.span_length / record.bay_width) if record.bay_width else 0
            record.no_of_spans = int(record.bay_length / record.span_width) if record.span_width else 0
            record.bottom_height = record.column_height
            record.arch_height = record.top_ridge_height - record.column_height
            record.gutter_length = record.span_length
    
    @api.depends('frame_component_ids.total_cost', 'truss_component_ids.total_cost', 
                 'side_screen_component_ids.total_cost', 'lower_component_ids.total_cost',
                 'asc_component_ids.total_cost')
    def _compute_section_totals(self):
        """Compute section totals - extensible by other modules"""
        for record in self:
            record.total_frame_cost = sum(record.frame_component_ids.mapped('total_cost'))
            record.total_truss_cost = sum(record.truss_component_ids.mapped('total_cost'))
            record.total_side_screen_cost = sum(record.side_screen_component_ids.mapped('total_cost')) 
            record.total_lower_cost = sum(record.lower_component_ids.mapped('total_cost'))
            record.total_asc_cost = sum(record.asc_component_ids.mapped('total_cost'))
            record.grand_total_cost = (record.total_frame_cost + record.total_truss_cost + 
                                     record.total_side_screen_cost + record.total_lower_cost +
                                     record.total_asc_cost)

    def _calculate_all_components(self):
        """Base method for calculating components - to be extended by other modules"""
        _logger.info("Base _calculate_all_components called - extend in other modules")
        pass
    
    def _get_length_master_value(self, length_master_field, default_value):
        """Helper method to get length from master field"""
        if length_master_field:
            try:
                return length_master_field.length_value
            except Exception:
                pass
        return default_value
    
    def _create_component_val(self, section, name, nos, length, length_master=None):
        """Helper to create component values"""
        val = {
            'green_master_id': self.id,
            'section': section,
            'name': name,
            'required': True,
            'nos': int(nos),
            'length': length,
            'is_calculated': True,
            'description': f"Auto-calculated component for {section} section",
        }
        
        if length_master:
            val.update({
                'length_master_id': length_master.id,
                'use_length_master': True,
            })
        
        return val
    
    def _clear_all_components(self):
        """Clear all component lines"""
        clear_vals = {
            'frame_component_ids': [(5, 0, 0)],
            'truss_component_ids': [(5, 0, 0)],
            'side_screen_component_ids': [(5, 0, 0)],
            'lower_component_ids': [(5, 0, 0)],
            'asc_component_ids': [(5, 0, 0)],
        }
        self.write(clear_vals)
    
    def _generate_component_key(self, section, name):
        """Generate unique key for component identification"""
        clean_name = name.strip().lower()
        
        name_mappings = {
            # ASC mappings
            'asc pipe support': 'asc_pipe_support',
            'front span asc pipes': 'front_span_asc_pipes',
            'back span asc pipes': 'back_span_asc_pipes',
            'front bay asc pipes': 'front_bay_asc_pipes',
            'back bay asc pipes': 'back_bay_asc_pipes',
            # Frame mappings
            'middle columns': 'middle_columns',
            'quadruple columns': 'quadruple_columns',
            'main columns': 'main_columns',
            'af main columns': 'af_main_columns',
            'thick columns': 'thick_columns',
            'main columns foundations': 'main_columns_foundations',
            'af main columns foundations': 'af_main_columns_foundations',
            'middle columns foundations': 'middle_columns_foundations',
            'quadruple columns foundations': 'quadruple_columns_foundations',
            'thick columns foundations': 'thick_columns_foundations',
            # Truss mappings
            'big arch': 'big_arch',
            'small arch': 'small_arch',
            'bottom chord anchor frame singular': 'bottom_chord_af_singular',
            'bottom chord anchor frame male': 'bottom_chord_af_male',
            'bottom chord anchor frame female': 'bottom_chord_af_female',
            'bottom chord inner line singular': 'bottom_chord_il_singular',
            'bottom chord inner line male': 'bottom_chord_il_male',
            'bottom chord inner line female': 'bottom_chord_il_female',
            'v support bottom chord': 'v_support_bottom_chord',
            'v support bottom chord (af)': 'v_support_bottom_chord_af',
            'arch support straight middle': 'arch_support_straight_middle',
            'arch support big (big arch)': 'arch_support_big_big_arch',
            'arch support big (small arch)': 'arch_support_big_small_arch',
            'arch support small for big arch': 'arch_support_small_big_arch',
            'arch support small for small arch': 'arch_support_small_small_arch',
            'vent support for big arch': 'vent_support_big_arch',
            'vent support for small arch': 'vent_support_small_arch',
            'big arch purlin': 'big_arch_purlin',
            'small arch purlin': 'small_arch_purlin',
            'gable purlin': 'gable_purlin',
            'bay side border purlin': 'bay_side_border_purlin',
            'span side border purlin': 'span_side_border_purlin',
            # Side Screen mappings
            'side screen roll up pipe': 'side_screen_roll_up_pipe',
            'side screen roll up pipe joiner': 'side_screen_roll_up_pipe_joiner',
            'side screen guard': 'side_screen_guard',
            'side screen guard box pipe': 'side_screen_guard_box_pipe',
            'side screen guard box h pipe': 'side_screen_guard_box_h_pipe',
            'side screen rollup handles': 'side_screen_rollup_handles',
            'side screen guard spacer': 'side_screen_guard_spacer',
            # Lower Section mappings
            'front & back column to column cross bracing x': 'front_back_cc_cross_bracing_x',
            'internal cc cross bracing x': 'internal_cc_cross_bracing_x',
            'cross bracing column to arch': 'cross_bracing_column_arch',
            'cross bracing column to bottom chord': 'cross_bracing_column_bottom',
            'arch middle purlin big arch': 'arch_middle_purlin_big_arch',
            'arch middle purlin small arch': 'arch_middle_purlin_small_arch',
            'gutter ippf full': 'gutter_ippf_full',
            'gutter funnel ippf': 'gutter_funnel_ippf',
            'gutter ippf drainage extension': 'gutter_ippf_drainage_extension',
            'gutter end cap': 'gutter_end_cap',
            'gutter continuous': 'gutter_continuous',
            'gutter purlin': 'gutter_purlin',
            'gutter purlin for extension': 'gutter_purlin_extension',
        }
        
        normalized_name = name_mappings.get(clean_name, clean_name.replace(' ', '_'))
        return f"{section}|{normalized_name}"

    def _save_component_selections_improved(self):
        """Save all component selections for restoration after recalculation"""
        saved_selections = {}
        
        all_components = (self.asc_component_ids + self.frame_component_ids + 
                         self.truss_component_ids + self.side_screen_component_ids + 
                         self.lower_component_ids)
        
        for component in all_components:
            component_key = self._generate_component_key(component.section, component.name)
            
            saved_selections[component_key] = {
                'original_name': component.name,
                'original_section': component.section,
                'pipe_id': component.pipe_id.id if component.pipe_id else False,
                'pipe_display_name': component.pipe_id.display_name if component.pipe_id else '',
                'use_length_master': component.use_length_master,
                'length_master_id': component.length_master_id.id if component.length_master_id else False,
                'length_master_value': component.length_master_id.length_value if component.length_master_id else 0.0,
                'custom_length': component.custom_length,
                'required': component.required,
                'notes': component.notes or '',
                'description': component.description or '',
                'section': component.section,
            }
        
        return saved_selections

    def _restore_component_selections_improved(self, saved_selections):
        """Restore component selections after recalculation"""
        if not saved_selections:
            return {
                'restored_count': 0,
                'failed_restorations': [],
                'total_saved': 0,
                'total_new_components': 0,
                'section_migrations': []
            }
        
        all_new_components = (self.asc_component_ids + self.frame_component_ids + 
                             self.truss_component_ids + self.side_screen_component_ids + 
                             self.lower_component_ids)
        
        restored_count = 0
        failed_restorations = []
        
        for component in all_new_components:
            component_key = self._generate_component_key(component.section, component.name)
            
            if component_key in saved_selections:
                selection_data = saved_selections[component_key]
                
                try:
                    update_vals = self._build_component_update_values(selection_data)
                    component.write(update_vals)
                    restored_count += 1
                    
                except Exception as e:
                    error_msg = f"Component: {component.name}, Error: {str(e)}"
                    failed_restorations.append(error_msg)
        
        return {
            'restored_count': restored_count,
            'failed_restorations': failed_restorations,
            'total_saved': len(saved_selections),
            'total_new_components': len(all_new_components),
        }

    def _build_component_update_values(self, selection_data):
        """Build update values for component restoration"""
        update_vals = {
            'required': selection_data['required'],
            'notes': selection_data['notes'],
            'use_length_master': selection_data['use_length_master'],
            'custom_length': selection_data['custom_length'],
        }
        
        if selection_data['description'] and not selection_data['description'].startswith('Auto-calculated'):
            update_vals['description'] = selection_data['description']
        
        if selection_data['pipe_id']:
            pipe_exists = self.env['pipe.management'].browse(selection_data['pipe_id']).exists()
            if pipe_exists:
                update_vals['pipe_id'] = selection_data['pipe_id']
        
        if selection_data['length_master_id']:
            length_master_exists = self.env['length.master'].browse(selection_data['length_master_id']).exists()
            if length_master_exists:
                update_vals['length_master_id'] = selection_data['length_master_id']
        
        return update_vals
        
        

    
    def _generate_recalculation_feedback(self, saved_selections, restoration_result, counts_before, counts_after):
        """Generate detailed feedback message after recalculation"""
        total_before = sum(counts_before.values())
        total_after = sum(counts_after.values())
        
        message_parts = [
            f"RECALCULATION SUMMARY:",
            f"",
            f"Components Before: {total_before} | Components After: {total_after}",
            f"",
            f"SECTION BREAKDOWN:",
        ]
        
        for section in ['asc', 'frame', 'truss', 'side_screen', 'lower']:
            section_name = section.upper().replace('_', ' ')
            before_count = counts_before.get(section, 0)
            after_count = counts_after.get(section, 0)
            
            if before_count > 0 or after_count > 0:
                change_indicator = "↗" if after_count > before_count else "↘" if after_count < before_count else "→"
                message_parts.append(f"  {change_indicator} {section_name}: {before_count} → {after_count}")
        
        message_parts.extend([
            f"",
            f"PIPE SELECTIONS:",
            f"  • Saved: {len(saved_selections)} selections",
            f"  • Restored: {restoration_result['restored_count']} selections",
        ])
        
        if restoration_result.get('failed_restorations'):
            message_parts.extend([
                f"  ⚠ Failed to restore: {len(restoration_result['failed_restorations'])} selections",
                f"     (Check logs for details)"
            ])
        
        new_components = restoration_result.get('total_new_components', 0) - restoration_result.get('restored_count', 0)
        if new_components > 0:
            message_parts.append(f"  ✨ New components: {new_components} (need pipe selection)")
        
        message_parts.extend([
            f"",
            f"Current Total Cost: {self.grand_total_cost:,.2f}",
            f"",
            f"✅ Recalculation completed successfully!"
        ])
        
        return "\n".join(message_parts)

    def action_recalculate_smart(self):
        """Smart recalculation that preserves pipe selections and custom settings"""
        try:
            # Save component selections before clearing
            saved_selections = self._save_component_selections_improved()
            
            # Count components before
            component_counts_before = {
                'asc': len(self.asc_component_ids or []),
                'frame': len(self.frame_component_ids or []),
                'truss': len(self.truss_component_ids or []),
                'side_screen': len(self.side_screen_component_ids or []),
                'lower': len(self.lower_component_ids or []),
            }
            
            # Clear and recalculate
            self._clear_all_components()
            self._calculate_all_components()
            
            # Restore selections
            restoration_result = self._restore_component_selections_improved(saved_selections)
            
            # Count components after
            component_counts_after = {
                'asc': len(self.asc_component_ids or []),
                'frame': len(self.frame_component_ids or []),
                'truss': len(self.truss_component_ids or []),
                'side_screen': len(self.side_screen_component_ids or []),
                'lower': len(self.lower_component_ids or []),
            }
            
            # Generate feedback message
            feedback_message = self._generate_recalculation_feedback(
                saved_selections, restoration_result, 
                component_counts_before, component_counts_after
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Smart Recalculation Complete',
                    'message': feedback_message,
                    'type': 'success',
                    'sticky': True,
                }
            }
        except Exception as e:
            _logger.error(f"Error during smart recalculation: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Recalculation failed: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def action_calculate_process(self):
        """Main calculation process - calls module-specific calculations"""
        try:
            # Clear existing components
            self._clear_all_components()
            
            # Call calculation method (will be extended by each module)
            self._calculate_all_components()
            
            # Count components
            total_components = len(self.frame_component_ids + self.truss_component_ids + 
                                 self.side_screen_component_ids + self.lower_component_ids +
                                 self.asc_component_ids)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Components Calculated',
                    'message': f'Successfully calculated {total_components} components.',
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Calculation Error',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def action_view_cost_summary(self):
        """View cost summary in popup"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Cost Summary - {self.customer or "Greenhouse Project"}',
            'res_model': 'component.line',
            'domain': [('green_master_id', '=', self.id)],
            'view_mode': 'tree',
            'target': 'new',
            'context': {
                'search_default_group_by_section': 1,
                'default_green_master_id': self.id,
                'create': False,
            }
        }
    
    def action_clear_all_components(self):
        """Clear all components without recalculation"""
        try:
            component_count = len(self.frame_component_ids + self.truss_component_ids + 
                                 self.side_screen_component_ids + self.lower_component_ids +
                                 self.asc_component_ids)
            
            self._clear_all_components()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Components Cleared',
                    'message': f'Deleted {component_count} components successfully.',
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to clear components: {str(e)}',
                    'type': 'danger',
                }
            }

    def action_clear_pipe_selections(self):
        """Clear all pipe selections but keep components"""
        try:
            count = 0
            all_components = (self.frame_component_ids + self.truss_component_ids + 
                             self.side_screen_component_ids + self.lower_component_ids +
                             self.asc_component_ids)
            
            for component in all_components:
                if component.pipe_id:
                    component.pipe_id = False
                    count += 1
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Pipes Cleared',
                    'message': f'Cleared pipe selections from {count} components.',
                    'type': 'info',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Failed to clear pipes: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def action_view_selection_summary(self):
        """View summary of pipe selections"""
        components_with_pipes = []
        components_without_pipes = []
        
        all_components = (self.frame_component_ids + self.truss_component_ids + 
                         self.side_screen_component_ids + self.lower_component_ids)
        
        if hasattr(self, 'asc_component_ids'):
            all_components = all_components + self.asc_component_ids
        
        for component in all_components:
            if component.pipe_id:
                components_with_pipes.append(f"{component.section.upper()}: {component.name}")
            else:
                components_without_pipes.append(f"{component.section.upper()}: {component.name}")
        
        message = f"""PIPE SELECTION SUMMARY:

Components WITH pipe selections ({len(components_with_pipes)}):
{chr(10).join(components_with_pipes) if components_with_pipes else 'None'}

Components WITHOUT pipe selections ({len(components_without_pipes)}):
{chr(10).join(components_without_pipes) if components_without_pipes else 'None'}

Total Components: {len(all_components)}
Completion: {len(components_with_pipes)}/{len(all_components)} ({int(len(components_with_pipes)/len(all_components)*100) if all_components else 0}%)"""
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Pipe Selection Summary',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
    
    def action_export_excel(self):
        """Export to Excel"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        export_url = f"{base_url}/greenhouse/export/excel/{self.id}"
        
        return {
            'type': 'ir.actions.act_url',
            'url': export_url,
            'target': 'new',
        }
    
    def print_report(self):
        """Print PDF report"""
        return self.env.ref('green2_base.report_print_green_master').report_action(self)
    
    def action_duplicate_project(self):
        """Duplicate project with all settings"""
        try:
            new_record = self.copy()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Project Duplicated',
                    'message': f'Successfully created copy: {new_record.customer}',
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Duplication Failed',
                    'message': f'Error: {str(e)}',
                    'type': 'danger',
                }
            }
    
    def action_open_bulk_pipe_assignment(self):
        """Open bulk pipe assignment wizard"""
        unassigned_count = self.env['component.line'].search_count([
            ('green_master_id', '=', self.id),
            ('pipe_id', '=', False)
        ])
        
        if unassigned_count == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Unassigned Components',
                    'message': 'All components already have pipes assigned!',
                    'type': 'info',
                }
            }
        
        wizard = self.env['bulk.pipe.assignment.wizard'].create({
            'green_master_id': self.id,
        })
        
        return {
            'name': f'Bulk Pipe Assignment - {unassigned_count} Unassigned Components',
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.pipe.assignment.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_green_master_id': self.id,
            }
        }
    
    def copy(self, default=None):
        """Copy project with all components"""
        if default is None:
            default = {}
        
        components_data = self._save_all_components()
        
        copy_default = {
            'customer': f"{self.customer} (Copy)" if self.customer else "Project Copy",
            'asc_component_ids': [],
            'frame_component_ids': [],
            'truss_component_ids': [],
            'side_screen_component_ids': [],
            'lower_component_ids': [],
        }
        copy_default.update(default)
        
        new_record = super(GreenMaster, self).copy(copy_default)
        self._restore_all_components(new_record, components_data)
        
        return new_record

    def _save_all_components(self):
        """Save all components data for duplication"""
        components_data = []
        
        all_components = (self.asc_component_ids + self.frame_component_ids + 
                         self.truss_component_ids + self.side_screen_component_ids + 
                         self.lower_component_ids)
        
        for component in all_components:
            component_data = {
                'section': component.section,
                'sequence': component.sequence,
                'name': component.name,
                'description': component.description,
                'required': component.required,
                'notes': component.notes,
                'nos': component.nos,
                'length': component.length,
                'use_length_master': component.use_length_master,
                'length_master_id': component.length_master_id.id if component.length_master_id else False,
                'custom_length': component.custom_length,
                'pipe_id': component.pipe_id.id if component.pipe_id else False,
                'is_calculated': component.is_calculated,
            }
            components_data.append(component_data)
        
        return components_data

    def _restore_all_components(self, new_record, components_data):
        """Restore components for duplicated project"""
        for comp_data in components_data:
            try:
                component_vals = {
                    'green_master_id': new_record.id,
                    'section': comp_data['section'],
                    'sequence': comp_data['sequence'],
                    'name': comp_data['name'],
                    'description': comp_data['description'],
                    'required': comp_data['required'],
                    'notes': comp_data['notes'],
                    'nos': comp_data['nos'],
                    'length': comp_data['length'],
                    'use_length_master': comp_data['use_length_master'],
                    'custom_length': comp_data['custom_length'],
                    'is_calculated': comp_data['is_calculated'],
                }
                
                if comp_data['length_master_id']:
                    component_vals['length_master_id'] = comp_data['length_master_id']
                
                if comp_data['pipe_id']:
                    component_vals['pipe_id'] = comp_data['pipe_id']
                
                self.env['component.line'].create(component_vals)
                
            except Exception as e:
                _logger.error(f"Failed to restore component {comp_data['name']}: {e}")
    
    @api.constrains('span_width', 'bay_width', 'total_span_length', 'total_bay_length')
    def _check_dimensions(self):
        for record in self:
            if record.span_width and record.total_span_length and record.span_width > record.total_span_length:
                raise ValidationError(_('Span width cannot be greater than total span length'))
            if record.bay_width and record.total_bay_length and record.bay_width > record.total_bay_length:
                raise ValidationError(_('Bay width cannot be greater than total bay length'))

    @api.constrains('column_height', 'top_ridge_height')
    def _check_heights(self):
        for record in self:
            if record.column_height and record.top_ridge_height and record.column_height >= record.top_ridge_height:
                raise ValidationError(_('Column height must be less than top ridge height'))
    
    # Add these validation methods to green2_base/models/green_master_base.py

    @api.constrains('total_span_length', 'total_bay_length', 'span_width', 'bay_width',
                    'top_ridge_height', 'column_height', 'big_arch_length', 'small_arch_length')
    def _check_positive_dimensions(self):
        """Validate that all critical dimensions are positive (greater than 0)"""
        for record in self:
            errors = []
            
            # Check Primary Dimensions
            if record.total_span_length <= 0:
                errors.append("Total Span Length must be greater than 0")
            
            if record.total_bay_length <= 0:
                errors.append("Total Bay Length must be greater than 0")
            
            if record.span_width <= 0:
                errors.append("Span Width must be greater than 0")
            
            if record.bay_width <= 0:
                errors.append("Bay Width must be greater than 0")
            
            # Check Height Configuration
            if record.top_ridge_height <= 0:
                errors.append("Top Ridge Height must be greater than 0")
            
            if record.column_height <= 0:
                errors.append("Column Height must be greater than 0")
            
            # Check Arch Lengths
            if record.big_arch_length <= 0:
                errors.append("Big Arch Length must be greater than 0")
            
            if record.small_arch_length <= 0:
                errors.append("Small Arch Length must be greater than 0")
            
            # Additional logical validations
            if record.top_ridge_height > 0 and record.column_height > 0:
                if record.column_height >= record.top_ridge_height:
                    errors.append("Column Height must be less than Top Ridge Height")
            
            if record.total_span_length > 0 and record.span_width > 0:
                if record.span_width > record.total_span_length:
                    errors.append("Span Width cannot be greater than Total Span Length")
            
            if record.total_bay_length > 0 and record.bay_width > 0:
                if record.bay_width > record.total_bay_length:
                    errors.append("Bay Width cannot be greater than Total Bay Length")
            
            # Raise validation error if any issues found
            if errors:
                from odoo.exceptions import ValidationError
                error_message = "Invalid Dimensions:\n\n" + "\n".join(["• " + error for error in errors])
                raise ValidationError(error_message)
                
                
                
    # Add to green2_base/models/green_master_base.py

    def action_auto_assign_pipes_by_pattern(self):
        """Smart auto-assignment based on component name patterns"""
        assignment_rules = {
            # Pattern matching for automatic assignment
            'Column': {'size': 100, 'thickness': 3.0},
            'Arch': {'size': 76, 'thickness': 2.0},
            'Purlin': {'size': 50, 'thickness': 2.0},
            'Support': {'size': 42, 'thickness': 2.0},
            'Bracing': {'size': 33, 'thickness': 1.5},
            'Guard': {'size': 25, 'thickness': 1.5},
        }
        
        unassigned_components = self.env['component.line'].search([
            ('green_master_id', '=', self.id),
            ('pipe_id', '=', False)
        ])
        
        assigned_count = 0
        for component in unassigned_components:
            for pattern, specs in assignment_rules.items():
                if pattern.lower() in component.name.lower():
                    matching_pipe = self.env['pipe.management'].search([
                        ('pipe_size.size_in_mm', '=', specs['size']),
                        ('wall_thickness.thickness_in_mm', '=', specs['thickness']),
                    ], limit=1)
                    
                    if matching_pipe:
                        component.pipe_id = matching_pipe.id
                        assigned_count += 1
                        break
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Auto-Assignment Complete',
                'message': f'Automatically assigned pipes to {assigned_count} components based on naming patterns.',
                'type': 'success' if assigned_count > 0 else 'info',
            }
        }

# Pipe Management Models
class PipeType(models.Model):
    _name = 'pipe.type'
    _description = 'Pipe Type'
    name = fields.Char(string='Pipe Type', required=True, tracking=True)

class PipeSize(models.Model):
    _name = 'pipe.size'
    _description = 'Pipe Size'
    name = fields.Char(string='Pipe Size', required=True, tracking=True)
    size_in_mm = fields.Float(string='Size in mm', required=True, tracking=True)

class PipeWallThickness(models.Model):
    _name = 'pipe.wall_thickness'
    _description = 'Pipe Wall Thickness'
    name = fields.Char(string='Wall Thickness', required=True, tracking=True)
    thickness_in_mm = fields.Float(string='Thickness in mm', required=True, tracking=True)

class Pipe(models.Model):
    _name = 'pipe.management'
    _description = 'Pipe Management'
    
    name = fields.Many2one('pipe.type', string='Pipe Type', required=True, tracking=True)
    pipe_size = fields.Many2one('pipe.size', string='Pipe Size (in mm)', required=True, tracking=True)
    wall_thickness = fields.Many2one('pipe.wall_thickness', string='Wall Thickness (in mm)', required=True, tracking=True)
    weight = fields.Float(string='Weight (in kg)', required=True, tracking=True)
    rate = fields.Float(string='Rate (per kg)', required=True, tracking=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('weight', 'rate')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.weight * record.rate
    
    @api.depends('pipe_size','wall_thickness')
    def _compute_display_name(self):
        for record in self:
            try:
                if record.name and record.pipe_size and record.wall_thickness:
                    record.display_name = f'{record.name.name} / Size: {record.pipe_size.size_in_mm} mm / Thickness: {record.wall_thickness.thickness_in_mm} mm'
                else:
                    record.display_name = record.name.name if record.name else 'Unnamed Pipe'
            except Exception:
                record.display_name = 'Unnamed Pipe'
    
    _sql_constraints = [
        ('unique_pipe_combination', 
         'unique(name, pipe_size, wall_thickness)', 
         'A pipe with this type, size, and wall thickness already exists.')
    ]
