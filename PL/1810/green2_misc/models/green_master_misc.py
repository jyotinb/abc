# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# At the top of the file, after imports

class AccessoriesComponentLine(models.Model):
    _inherit = 'accessories.component.line'
    
    section = fields.Selection(
        selection_add=[('misc', 'Miscellaneous')],
        ondelete={'misc': 'cascade'}
    )

class GreenMasterMisc(models.Model):
    _inherit = 'green.master'
    
    # =============================================
    # MISCELLANEOUS CONFIGURATION FIELDS
    # =============================================
    calculate_misc_components = fields.Boolean(
        'Calculate Miscellaneous Components',
        default=False,
        tracking=True,
        help="Enable miscellaneous component calculations"
    )
    
    # Silicon Configuration
    calculate_silicon = fields.Boolean(
        'Calculate Silicon',
        default=False,
        tracking=True,
        help="Calculate silicon based on gutter configuration"
    )
    
    silicon_unit_price = fields.Float(
        'Silicon Unit Price',
        default=0.0,
        tracking=True,
        help="Price per silicon unit"
    )
    
    # Drainage Pipe Configuration
    calculate_drainage_pipe = fields.Boolean(
        'Calculate Drainage Pipe',
        default=False,
        tracking=True,
        help="Calculate drainage pipes"
    )
    
    drainage_pipe_option_id = fields.Many2one(
        'drainage.pipe.option',
        string='Drainage Pipe Length',
        tracking=True,
        help="Select drainage pipe length option"
    )
    
    funnel_pipe_size = fields.Float(
        'Funnel Pipe Size (mm)',
        default=0.0,
        tracking=True,
        help="Size of funnel pipe for drainage and clamps"
    )
    
    # Hose Clamp Configuration
    calculate_hose_clamp = fields.Boolean(
        'Calculate Hose Clamp',
        default=False,
        tracking=True,
        help="Calculate hose clamps"
    )
    
    hose_clamp_unit_price = fields.Float(
        'Hose Clamp Unit Price',
        default=0.0,
        tracking=True,
        help="Price per hose clamp unit"
    )
    
    # Sliding Door Configuration
    calculate_sliding_door = fields.Boolean(
        'Calculate Sliding Door',
        default=False,
        tracking=True,
        help="Calculate sliding doors"
    )
    
    door_model_id = fields.Many2one(
        'door.model',
        string='Door Model',
        tracking=True,
        help="Select door model for sliding doors"
    )
    
    # Computed field for number of doors
    no_of_sliding_doors = fields.Integer(
        'Number of Sliding Doors',
        compute='_compute_no_of_sliding_doors',
        store=True,
        help="Calculated as: (Standalone Doors × 1) + (Entry Chambers × 2)"
    )
    
    # Miscellaneous component collections
    misc_component_ids = fields.One2many(
        'accessories.component.line',
        'green_master_id',
        domain=[('section', '=', 'misc')],
        string='Miscellaneous Components'
    )
    
    # Cost field for miscellaneous
    total_misc_cost = fields.Float(
        'Total Miscellaneous Cost',
        compute='_compute_misc_cost',
        store=True,
        tracking=True
    )
    
    @api.depends('standalone_doors_count', 'entry_chambers_count')
    def _compute_no_of_sliding_doors(self):
        """
        Calculate number of sliding doors
        Formula: (Standalone Doors × 1) + (Entry Chambers × 2)
        """
        for record in self:
            standalone = record.standalone_doors_count or 0
            chambers = record.entry_chambers_count or 0
            record.no_of_sliding_doors = (standalone * 1) + (chambers * 2)
    
    @api.depends('misc_component_ids.total_cost')
    def _compute_misc_cost(self):
        """Compute total cost for miscellaneous components"""
        for record in self:
            record.total_misc_cost = sum(record.misc_component_ids.mapped('total_cost'))
    
    def _calculate_all_accessories(self):
        """Extend to add miscellaneous calculations"""
        super()._calculate_all_accessories()
        if self.calculate_misc_components:
            self._calculate_misc_components()
    
    def _calculate_misc_components(self):
        """Calculate miscellaneous components"""
        _logger.info("=== CALCULATING MISCELLANEOUS COMPONENTS ===")
        
        # Clear existing miscellaneous components
        existing_misc = self.env['accessories.component.line'].search([
            ('green_master_id', '=', self.id),
            ('section', '=', 'misc')
        ])
        if existing_misc:
            existing_misc.unlink()
        
        # Calculate each miscellaneous component
        if self.calculate_silicon:
            self._calculate_silicon_component()
        
        if self.calculate_drainage_pipe:
            self._calculate_drainage_pipe_component()
        
        if self.calculate_hose_clamp:
            self._calculate_hose_clamp_component()
        
        if self.calculate_sliding_door:
            self._calculate_sliding_door_component()
        
        _logger.info(f"Miscellaneous calculation complete. Total cost: {self.total_misc_cost}")
    
    def _calculate_silicon_component(self):
        """
        Calculate Silicon component
        
        Logic:
        - Only if Gutter is IPPF
        - If Last Span Gutter is Yes: Nos = no of spans + 1
        - If Last Span Gutter is No: Nos = no of spans - 1
        """
        # Check if gutter type is IPPF
        if self.gutter_type != 'ippf':
            _logger.info("Silicon not applicable (Gutter type is not IPPF)")
            return
        
        if self.no_of_spans <= 0:
            _logger.warning("Insufficient data for Silicon calculation")
            return
        
        # Calculate Nos based on last span gutter
        if self.last_span_gutter:
            nos = self.no_of_spans + 1
        else:
            nos = self.no_of_spans - 1
        
        if nos <= 0:
            _logger.warning("Invalid number of silicon units calculated")
            return
        
        # Create component
        component_name = "Silicon"
        size_spec = "For IPPF Gutter"
        
        self._create_misc_component(
            'misc',
            component_name,
            nos,
            size_spec,
            self.silicon_unit_price
        )
        
        _logger.info(f"Created Silicon: {nos} units @ ₹{self.silicon_unit_price}/unit")
    
    def _calculate_drainage_pipe_component(self):
        """
        Calculate Drainage Pipe component
        
        Logic:
        - Size = Funnel Pipe Size
        - Length = Selected Option (6m/7m/8m)
        - Nos = No of Gutter Funnel
        """
        if not self.drainage_pipe_option_id:
            _logger.warning("Drainage pipe option not selected")
            return
        
        if self.funnel_pipe_size <= 0:
            _logger.warning("Funnel pipe size not set")
            return
        
        # Get number of gutter funnels from lower components
        no_of_gutter_funnel = self._get_gutter_funnel_count()
        
        if no_of_gutter_funnel <= 0:
            _logger.warning("No gutter funnels found")
            return
        
        # Get selected length and price
        length = self.drainage_pipe_option_id.length_value
        unit_price = self.drainage_pipe_option_id.unit_price
        
        # Create component
        component_name = "Drainage Pipe"
        size_spec = f"Size: {self.funnel_pipe_size}mm, Length: {length}m"
        
        self._create_misc_component(
            'misc',
            component_name,
            no_of_gutter_funnel,
            size_spec,
            unit_price
        )
        
        _logger.info(f"Created Drainage Pipe: {no_of_gutter_funnel} units, {length}m @ ₹{unit_price}/unit")
    
    def _calculate_hose_clamp_component(self):
        """
        Calculate Hose Clamp component
        
        Logic:
        - Size = Funnel Pipe Size
        - Nos = No of Gutter Funnel
        """
        if self.funnel_pipe_size <= 0:
            _logger.warning("Funnel pipe size not set for hose clamp")
            return
        
        # Get number of gutter funnels
        no_of_gutter_funnel = self._get_gutter_funnel_count()
        
        if no_of_gutter_funnel <= 0:
            _logger.warning("No gutter funnels found for hose clamp")
            return
        
        # Create component
        component_name = "Hose Clamp"
        size_spec = f"Size: {self.funnel_pipe_size}mm"
        
        self._create_misc_component(
            'misc',
            component_name,
            no_of_gutter_funnel,
            size_spec,
            self.hose_clamp_unit_price
        )
        
        _logger.info(f"Created Hose Clamp: {no_of_gutter_funnel} units @ ₹{self.hose_clamp_unit_price}/unit")
    
    def _calculate_sliding_door_component(self):
        """
        Calculate Sliding Door component
        
        Logic:
        - No of Doors = (Standalone Doors × 1) + (Entry Chambers × 2)
        - Door Model from selection
        """
        if not self.door_model_id:
            _logger.warning("Door model not selected")
            return
        
        if self.no_of_sliding_doors <= 0:
            _logger.info("No sliding doors to calculate")
            return
        
        # Get door model details
        door_model = self.door_model_id
        unit_price = door_model.unit_price
        
        # Create component
        component_name = f"Sliding Door - {door_model.name}"
        size_spec = f"Model: {door_model.code or door_model.name}"
        
        self._create_misc_component(
            'misc',
            component_name,
            self.no_of_sliding_doors,
            size_spec,
            unit_price
        )
        
        _logger.info(f"Created Sliding Door: {self.no_of_sliding_doors} units, Model: {door_model.name} @ ₹{unit_price}/unit")
    
    def _get_gutter_funnel_count(self):
        """Get count of gutter funnels from lower components"""
        if not hasattr(self, 'lower_component_ids'):
            return 0
        
        # Search for gutter funnel components
        funnel_components = self.lower_component_ids.filtered(
            lambda c: 'Gutter Funnel' in c.name or 'funnel' in c.name.lower()
        )
        
        if funnel_components:
            # Return the nos (quantity) of the first funnel component found
            return funnel_components[0].nos
        
        return 0
    
    def _create_misc_component(self, section, name, nos, size_spec, unit_price):
        """
        Create miscellaneous component
        
        Args:
            section: Component section ('misc')
            name: Component name
            nos: Number of units
            size_spec: Size specification string
            unit_price: Price per unit
        """
        try:
            vals = {
                'green_master_id': self.id,
                'section': section,
                'name': name,
                'nos': int(nos),
                'size_specification': size_spec,
                'unit_price': unit_price,
                'is_calculated': True,
                'description': f"Auto-calculated miscellaneous component: {nos} units @ ₹{unit_price}/unit",
            }
            
            component = self.env['accessories.component.line'].create(vals)
            
            _logger.info(f"Created misc component: {name} - {nos} units at ₹{unit_price}/unit")
            return component
            
        except Exception as e:
            _logger.error(f"Error creating misc component {name}: {e}")
            return None
    
    @api.onchange('calculate_misc_components')
    def _onchange_calculate_misc_components(self):
        """Handle changes to miscellaneous calculation flag"""
        if not self.calculate_misc_components:
            self.calculate_silicon = False
            self.calculate_drainage_pipe = False
            self.calculate_hose_clamp = False
            self.calculate_sliding_door = False
    
    def action_calculate_misc(self):
        """Action to calculate only miscellaneous components"""
        for record in self:
            try:
                if not record.calculate_misc_components:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Miscellaneous Not Enabled',
                            'message': 'Please enable "Calculate Miscellaneous Components" first.',
                            'type': 'warning',
                        }
                    }
                
                # Clear existing miscellaneous components
                existing_misc = self.env['accessories.component.line'].search([
                    ('green_master_id', '=', record.id),
                    ('section', '=', 'misc')
                ])
                if existing_misc:
                    existing_misc.unlink()
                
                # Calculate miscellaneous
                record._calculate_misc_components()
                
                component_count = len(record.misc_component_ids)
                total_cost = record.total_misc_cost
                
                message = f"MISCELLANEOUS CALCULATION COMPLETED:\n\n"
                message += f"Components generated: {component_count}\n"
                message += f"Total Miscellaneous Cost: {total_cost:.2f}\n\n"
                
                components_list = []
                if record.calculate_silicon:
                    components_list.append("✓ Silicon")
                if record.calculate_drainage_pipe:
                    components_list.append("✓ Drainage Pipe")
                if record.calculate_hose_clamp:
                    components_list.append("✓ Hose Clamp")
                if record.calculate_sliding_door:
                    components_list.append(f"✓ Sliding Door ({record.no_of_sliding_doors} units)")
                
                if components_list:
                    message += "Components Calculated:\n" + "\n".join(components_list)
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Miscellaneous Calculated Successfully',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
            except Exception as e:
                _logger.error(f"Error in miscellaneous calculation: {e}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Miscellaneous Calculation Error',
                        'message': f'Error occurred: {str(e)}',
                        'type': 'danger',
                    }
                }
    
    @api.constrains('funnel_pipe_size', 'silicon_unit_price', 'hose_clamp_unit_price')
    def _check_misc_values(self):
        """Validate miscellaneous configuration values"""
        for record in self:
            if record.calculate_drainage_pipe or record.calculate_hose_clamp:
                if record.funnel_pipe_size <= 0:
                    raise ValidationError("Funnel pipe size must be greater than 0")
            
            if record.calculate_silicon and record.silicon_unit_price < 0:
                raise ValidationError("Silicon unit price cannot be negative")
            
            if record.calculate_hose_clamp and record.hose_clamp_unit_price < 0:
                raise ValidationError("Hose clamp unit price cannot be negative")
