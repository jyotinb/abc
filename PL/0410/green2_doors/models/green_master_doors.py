from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class GreenMasterDoors(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # DOOR CONFIGURATION FIELDS
    # =============================================
    has_doors = fields.Boolean('Include Doors', default=False, tracking=True,
                              help="Enable door and chamber calculations")
    
    standalone_doors_count = fields.Integer('Standalone Doors (X)', default=0, tracking=True,
                                          help="Number of simple door openings")
    
    entry_chambers_count = fields.Integer('Entry Chambers (Y)', default=0, tracking=True,
                                        help="Number of full entry chambers with columns and purlins")
    
    # Chamber Configuration
    chamber_depth = fields.Float('Chamber Depth (m)', default=2.0, tracking=True,
                                help="Depth of entry chambers for purlin calculations")
    
    chamber_column_length = fields.Many2one(
        'length.master', 
        string='Chamber Column Length',
        domain="[('available_for_fields.name', '=', 'length_chamber_column'), ('active', '=', True)]",
        tracking=True,
        help="Selectable length for front columns in chambers"
    )
    
    # Tractor Door Configuration  
    tractor_door_type = fields.Selection([
        ('none', 'None'),
        ('vertical', 'Vertical'),
        ('openable', 'Openable'),
    ], string='Tractor Door Type', default='none', tracking=True,
       help="Type of tractor door installation")
    
    tractor_door_height = fields.Float('Tractor Door Height (m)', default=3.0, tracking=True,
                                     help="Height for tractor door vertical pipes")
    
    nos_tractor_doors = fields.Integer('Number of Tractor Doors', default=0, tracking=True,
                                     help="Total number of tractor doors to install")
    
    # =============================================
    # LENGTH MASTER FIELDS FOR DOOR COMPONENTS
    # =============================================
    length_column_pipe = fields.Many2one(
        'length.master', 
        string='Length for Door Column Pipe',
        domain="[('available_for_fields.name', '=', 'length_column_pipe'), ('active', '=', True)]",
        tracking=True
    )
    
    length_purlin_pipe = fields.Many2one(
        'length.master', 
        string='Length for Door Purlin Pipe',
        domain="[('available_for_fields.name', '=', 'length_purlin_pipe'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_purlin = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door Purlin',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_purlin'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_h_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door H Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_h_pipes'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_big_h_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door Big H Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_big_h_pipes'), ('active', '=', True)]",
        tracking=True
    )
    
    length_tractor_door_v_pipes = fields.Many2one(
        'length.master', 
        string='Length for Tractor Door V Pipes',
        domain="[('available_for_fields.name', '=', 'length_tractor_door_v_pipes'), ('active', '=', True)]",
        tracking=True
    )
    
    # =============================================
    # DOOR COMPONENT TOTALS
    # =============================================
    door_component_ids = fields.One2many('component.line', 'green_master_id', 
                                        domain=[('section', '=', 'doors')], 
                                        string='Door Components')
    
    total_door_components = fields.Integer('Total Door Components (X + Y)', 
                                         compute='_compute_door_totals', store=True,
                                         help="Total doors and chambers combined")
    
    total_chamber_components = fields.Integer('Total Chamber Components (Y)', 
                                            compute='_compute_door_totals', store=True,
                                            help="Entry chambers only")
    
    total_door_cost = fields.Float('Total Door Cost', 
                                  compute='_compute_door_totals', store=True, tracking=True)

    # =============================================
    # COMPUTED METHODS
    # =============================================
    @api.depends('standalone_doors_count', 'entry_chambers_count', 'door_component_ids.total_cost')
    def _compute_door_totals(self):
        """Compute door totals using the formula: Door Components = X + Y, Chamber Components = Y"""
        for record in self:
            record.total_door_components = record.standalone_doors_count + record.entry_chambers_count
            record.total_chamber_components = record.entry_chambers_count
            record.total_door_cost = sum(record.door_component_ids.mapped('total_cost'))
    
    @api.depends('door_component_ids.total_cost', 'asc_component_ids.total_cost', 
                 'frame_component_ids.total_cost', 'truss_component_ids.total_cost', 
                 'side_screen_component_ids.total_cost', 'lower_component_ids.total_cost')
    def _compute_section_totals(self):
        """Override to include door costs in grand total"""
        super()._compute_section_totals()
        for record in self:
            # Add door costs to the grand total
            record.grand_total_cost = (
                record.total_asc_cost + 
                record.total_frame_cost + 
                record.total_truss_cost + 
                record.total_side_screen_cost + 
                record.total_lower_cost + 
                record.total_door_cost
            )
    
    # =============================================
    # ONCHANGE METHODS
    # =============================================
    @api.onchange('has_doors')
    def _onchange_has_doors(self):
        """Reset door counts when doors disabled"""
        if not self.has_doors:
            self.standalone_doors_count = 0
            self.entry_chambers_count = 0
            self.tractor_door_type = 'none'
            self.nos_tractor_doors = 0

    @api.onchange('tractor_door_type')
    def _onchange_tractor_door_type(self):
        """Reset tractor door count when type is none"""
        if self.tractor_door_type == 'none':
            self.nos_tractor_doors = 0

    # =============================================
    # CORE CALCULATION METHODS
    # =============================================
    def _calculate_all_components(self):
        """Extend base calculation to add door components"""
        super()._calculate_all_components()
        if self.has_doors:
            self._calculate_door_components()

    def _calculate_door_components(self):
        """Calculate door components based on configuration"""
        if not self.has_doors:
            return
            
        component_vals = []
        
        # =============================================
        # STANDALONE DOORS (X) CALCULATIONS
        # =============================================
        if self.standalone_doors_count > 0:
            # Door Column Pipe
            column_pipe_length = self._get_length_master_value(self.length_column_pipe, 3.5)
            component_vals.append(self._create_component_val(
                'doors', 'Door Column Pipe', 
                self.standalone_doors_count, 
                column_pipe_length, 
                self.length_column_pipe
            ))
            
            # Door Purlin Pipe
            purlin_pipe_length = self._get_length_master_value(self.length_purlin_pipe, self.bay_width)
            component_vals.append(self._create_component_val(
                'doors', 'Door Purlin Pipe', 
                self.standalone_doors_count, 
                purlin_pipe_length, 
                self.length_purlin_pipe
            ))
        
        # =============================================
        # ENTRY CHAMBERS (Y) CALCULATIONS
        # =============================================
        if self.entry_chambers_count > 0:
            # Get selected column length or default
            selected_column_length = self.chamber_column_length.length_value if self.chamber_column_length else 3.0
            
            # Door Front Column: 3 pieces per chamber
            component_vals.append(self._create_component_val(
                'doors', 'Door Front Column', 
                self.entry_chambers_count * 3,
                selected_column_length, 
                self.chamber_column_length
            ))
            
            # Door Front Purlin: 1 piece × Bay Width per chamber
            component_vals.append(self._create_component_val(
                'doors', 'Door Front Purlin', 
                self.entry_chambers_count, 
                self.bay_width
            ))
            
            # Door Side Purlin: 2 pieces × Chamber Depth per chamber
            component_vals.append(self._create_component_val(
                'doors', 'Door Side Purlin', 
                self.entry_chambers_count * 2,
                self.chamber_depth
            ))
            
            # Door Bottom Purlin: 2 pieces × (Chamber Depth + 0.25) per chamber
            component_vals.append(self._create_component_val(
                'doors', 'Door Bottom Purlin', 
                self.entry_chambers_count * 2,
                self.chamber_depth + 0.25
            ))
        
        # =============================================
        # TRACTOR DOOR CALCULATIONS
        # =============================================
        if self.tractor_door_type != 'none' and self.nos_tractor_doors > 0:
            
            if self.tractor_door_type == 'vertical':
                # VERTICAL TRACTOR DOOR COMPONENTS
                
                # Tractor Door Purlin
                tractor_purlin_length = self._get_length_master_value(
                    self.length_tractor_door_purlin, self.bay_width)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door Purlin', 
                    self.nos_tractor_doors, 
                    tractor_purlin_length,
                    self.length_tractor_door_purlin
                ))
                
                # Tractor Door H Pipes
                tractor_h_pipes_length = self._get_length_master_value(
                    self.length_tractor_door_h_pipes, self.bay_width / 2)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door H Pipes', 
                    self.nos_tractor_doors * 2, 
                    tractor_h_pipes_length,
                    self.length_tractor_door_h_pipes
                ))
                
                # Tractor Door Big H Pipes
                tractor_big_h_pipes_length = self._get_length_master_value(
                    self.length_tractor_door_big_h_pipes, self.bay_width)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door Big H Pipes', 
                    self.nos_tractor_doors * 2, 
                    tractor_big_h_pipes_length,
                    self.length_tractor_door_big_h_pipes
                ))
                
                # Tractor Door V Pipes
                tractor_v_pipes_length = self._get_length_master_value(
                    self.length_tractor_door_v_pipes, self.tractor_door_height)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door V Pipes', 
                    self.nos_tractor_doors * 3, 
                    tractor_v_pipes_length,
                    self.length_tractor_door_v_pipes
                ))
                
            elif self.tractor_door_type == 'openable':
                # OPENABLE TRACTOR DOOR COMPONENTS
                
                # Tractor Door Purlin
                tractor_purlin_length = self._get_length_master_value(
                    self.length_tractor_door_purlin, self.bay_width)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door Purlin', 
                    self.nos_tractor_doors, 
                    tractor_purlin_length,
                    self.length_tractor_door_purlin
                ))
                
                # Tractor Door H Pipes: 6 pieces for openable
                tractor_h_pipes_length = self._get_length_master_value(
                    self.length_tractor_door_h_pipes, self.bay_width / 2)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door H Pipes', 
                    self.nos_tractor_doors * 6, 
                    tractor_h_pipes_length,
                    self.length_tractor_door_h_pipes
                ))
                
                # Tractor Door V Pipes: 4 pieces for openable
                tractor_v_pipes_length = self._get_length_master_value(
                    self.length_tractor_door_v_pipes, self.tractor_door_height)
                component_vals.append(self._create_component_val(
                    'doors', 'Tractor Door V Pipes', 
                    self.nos_tractor_doors * 4, 
                    tractor_v_pipes_length,
                    self.length_tractor_door_v_pipes
                ))
        
        # Create all door component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created door component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating door component {val.get('name', 'Unknown')}: {e}")

    # =============================================
    # VALIDATION METHODS
    # =============================================
    @api.constrains('standalone_doors_count', 'entry_chambers_count', 'nos_tractor_doors')
    def _check_door_counts(self):
        """Validate door configuration"""
        for record in self:
            if record.has_doors:
                if record.standalone_doors_count < 0:
                    raise ValidationError("Standalone doors count cannot be negative")
                if record.entry_chambers_count < 0:
                    raise ValidationError("Entry chambers count cannot be negative")
                if record.nos_tractor_doors < 0:
                    raise ValidationError("Tractor doors count cannot be negative")
                
                # At least one type should be configured if doors are enabled
                total_doors = record.standalone_doors_count + record.entry_chambers_count + record.nos_tractor_doors
                if total_doors == 0:
                    raise ValidationError("At least one door type must be configured when doors are enabled")

    @api.constrains('chamber_depth', 'tractor_door_height')
    def _check_door_dimensions(self):
        """Validate door dimensions"""
        for record in self:
            if record.chamber_depth <= 0:
                raise ValidationError("Chamber depth must be greater than 0")
            if record.tractor_door_height <= 0:
                raise ValidationError("Tractor door height must be greater than 0")


# =============================================
# EXTEND COMPONENT LINE TO ADD DOORS SECTION
# =============================================
class ComponentLine(models.Model):
    _inherit = 'component.line'
    
    # Add 'doors' to existing section selection
    section = fields.Selection(
        selection_add=[('doors', 'Door Components')],
        ondelete={'doors': 'cascade'}
    )
