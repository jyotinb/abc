from odoo import models, fields, api
from math import sqrt
import logging

_logger = logging.getLogger(__name__)

class GreenMasterASC(models.Model):
    _inherit = 'green.master'
    
    # ASC Configuration Fields
    is_side_coridoors = fields.Boolean('Is ASC', default=False, tracking=True)
    width_front_span_coridoor = fields.Float('Width Front Span ASC', default=0.00, tracking=True)
    width_back_span_coridoor = fields.Float('Width Back Span ASC', default=0.00, tracking=True)
    width_front_bay_coridoor = fields.Float('Width Left Bay ASC', default=0.00, tracking=True)
    width_back_bay_coridoor = fields.Float('Width Right Bay ASC', default=0.00, tracking=True)
    support_hockeys = fields.Integer('Support per Hockey', default=0, tracking=True)
    
    # Length Master Field for ASC
    length_support_hockeys = fields.Many2one(
        'length.master', 
        string='Length for Support Hockey',
        domain="[('available_for_fields.name', '=', 'length_support_hockeys'), ('active', '=', True)]",
        tracking=True
    )
    
    @api.depends('total_span_length', 'total_bay_length', 'width_front_span_coridoor', 
                 'width_back_span_coridoor', 'width_front_bay_coridoor', 'width_back_bay_coridoor',
                 'span_width', 'bay_width', 'column_height', 'top_ridge_height')
    def _compute_calculated_dimensions(self):
        """Override to include ASC calculations"""
        for record in self:
            # Calculate effective lengths after ASC corridors
            record.span_length = record.total_span_length - (record.width_front_bay_coridoor + record.width_back_bay_coridoor)
            record.bay_length = record.total_bay_length - (record.width_front_span_coridoor + record.width_back_span_coridoor)
            
            # Structure size includes ASC areas
            record.structure_size = (
                (record.span_length + record.width_front_bay_coridoor + record.width_back_bay_coridoor) *
                (record.bay_length + record.width_front_span_coridoor + record.width_back_span_coridoor)
            )
            
            record.no_of_bays = int(record.span_length / record.bay_width) if record.bay_width else 0
            record.no_of_spans = int(record.bay_length / record.span_width) if record.span_width else 0
            
            record.bottom_height = record.column_height
            record.arch_height = record.top_ridge_height - record.column_height
            record.gutter_length = record.span_length
    
    def _calculate_all_components(self):
        """Extend calculation to add ASC components"""
        super()._calculate_all_components()
        if self.is_side_coridoors:
            self._calculate_asc_components()
    
    def _calculate_asc_components(self):
        """Calculate ASC-specific components"""
        component_vals = []
        
        # Calculate hockey counts
        no_asc = 0
        if self.width_front_span_coridoor > 0:
            no_asc += 1
        if self.width_back_span_coridoor > 0:
            no_asc += 1
        if self.width_front_bay_coridoor > 0:
            no_asc += 1
        if self.width_back_bay_coridoor > 0:
            no_asc += 1
        
        no_front_span_coridoor_hockeys = 0
        if self.width_front_span_coridoor > 0:
            no_front_span_coridoor_hockeys = ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
        
        no_back_span_coridoor_hockeys = 0
        if self.width_back_span_coridoor > 0:
            no_back_span_coridoor_hockeys = ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
        
        no_front_bay_coridoor_hockeys = 0
        if self.width_front_bay_coridoor > 0:
            no_front_bay_coridoor_hockeys = (self.span_length / self.bay_width) + 1
        
        no_back_bay_coridoor_hockeys = 0
        if self.width_back_bay_coridoor > 0:
            no_back_bay_coridoor_hockeys = (self.span_length / self.bay_width) + 1
        
        no_total_hockeys = (no_front_span_coridoor_hockeys + no_back_span_coridoor_hockeys + 
                           no_front_bay_coridoor_hockeys + no_back_bay_coridoor_hockeys)
        
        # Create ASC Support components
        if self.support_hockeys > 0 and no_total_hockeys > 0:
            support_length = self._get_length_master_value(self.length_support_hockeys, 1.5)
            component_vals.append(self._create_component_val(
                'asc', 'ASC Pipe Support', 
                self.support_hockeys * int(no_total_hockeys), 
                support_length, 
                self.length_support_hockeys
            ))
        
        # Create ASC Pipe components
        if no_front_span_coridoor_hockeys > 0:
            length_front_span = 1 + sqrt(self.width_front_span_coridoor ** 2 + self.column_height ** 2)
            component_vals.append(self._create_component_val(
                'asc', 'Front Span ASC Pipes', 
                int(no_front_span_coridoor_hockeys), 
                length_front_span
            ))
        
        if no_back_span_coridoor_hockeys > 0:
            length_back_span = 1 + sqrt(self.width_back_span_coridoor ** 2 + self.column_height ** 2)
            component_vals.append(self._create_component_val(
                'asc', 'Back Span ASC Pipes', 
                int(no_back_span_coridoor_hockeys), 
                length_back_span
            ))
        
        if no_front_bay_coridoor_hockeys > 0:
            length_front_bay = 1 + sqrt(self.width_front_bay_coridoor ** 2 + self.column_height ** 2)
            component_vals.append(self._create_component_val(
                'asc', 'Front Bay ASC Pipes', 
                int(no_front_bay_coridoor_hockeys), 
                length_front_bay
            ))
        
        if no_back_bay_coridoor_hockeys > 0:
            length_back_bay = 1 + sqrt(self.width_back_bay_coridoor ** 2 + self.column_height ** 2)
            component_vals.append(self._create_component_val(
                'asc', 'Back Bay ASC Pipes', 
                int(no_back_bay_coridoor_hockeys), 
                length_back_bay
            ))
        
        # Create all ASC component lines
        for val in component_vals:
            try:
                self.env['component.line'].create(val)
                _logger.info(f"Created ASC component: {val['name']} - Nos: {val['nos']} - Length: {val['length']}")
            except Exception as e:
                _logger.error(f"Error creating ASC component {val.get('name', 'Unknown')}: {e}")
    
    def _calculate_total_hockeys(self):
        """Override side screen's hockey calculation with actual ASC values"""
        if not self.is_side_coridoors:
            return 0
        
        no_total_hockeys = 0
        
        if self.width_front_span_coridoor > 0:
            no_total_hockeys += ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
        
        if self.width_back_span_coridoor > 0:
            no_total_hockeys += ((self.bay_length / self.span_width) * (int(self.no_column_big_frame) + 1)) + 1
        
        if self.width_front_bay_coridoor > 0:
            no_total_hockeys += (self.span_length / self.bay_width) + 1
        
        if self.width_back_bay_coridoor > 0:
            no_total_hockeys += (self.span_length / self.bay_width) + 1
        
        return int(no_total_hockeys)
    
    @api.constrains('total_span_length', 'width_front_bay_coridoor', 'width_back_bay_coridoor', 
                    'bay_width', 'total_bay_length', 'width_front_span_coridoor', 
                    'width_back_span_coridoor', 'span_width', 'is_side_coridoors')
    def _check_span_bay_asc_dimensions(self):
        """Validate that span and bay calculations result in integer values when ASC is enabled"""
        for record in self:
            # First check if basic dimensions are valid
            if (record.total_span_length <= 0 or record.total_bay_length <= 0 or 
                record.span_width <= 0 or record.bay_width <= 0):
                return
            
            # Only validate if ASC is enabled and relevant values are set
            if record.is_side_coridoors:
                errors = []
                
                # Validation 1: Check bay calculation
                if record.bay_width and record.bay_width > 0:
                    effective_span_length = (record.total_span_length - 
                                            record.width_front_bay_coridoor - 
                                            record.width_back_bay_coridoor)
                    
                    if effective_span_length <= 0:
                        errors.append("Total Span Length minus ASC widths (Left Bay + Right Bay) must be greater than 0")
                    elif effective_span_length > 0:
                        bay_result = effective_span_length / record.bay_width
                        
                        if abs(bay_result - round(bay_result)) > 0.001:
                            errors.append(
                                f"Bay calculation error: ({record.total_span_length} - "
                                f"{record.width_front_bay_coridoor} - {record.width_back_bay_coridoor}) / "
                                f"{record.bay_width} = {bay_result:.2f} (must be integer)"
                            )
                
                # Validation 2: Check span calculation
                if record.span_width and record.span_width > 0:
                    effective_bay_length = (record.total_bay_length - 
                                           record.width_front_span_coridoor - 
                                           record.width_back_span_coridoor)
                    
                    if effective_bay_length <= 0:
                        errors.append("Total Bay Length minus ASC widths (Front Span + Back Span) must be greater than 0")
                    elif effective_bay_length > 0:
                        span_result = effective_bay_length / record.span_width
                        
                        if abs(span_result - round(span_result)) > 0.001:
                            errors.append(
                                f"Span calculation error: ({record.total_bay_length} - "
                                f"{record.width_front_span_coridoor} - {record.width_back_span_coridoor}) / "
                                f"{record.span_width} = {span_result:.2f} (must be integer)"
                            )
                
                if errors:
                    from odoo.exceptions import ValidationError
                    error_message = "Span, Bay, ASC not Proper\n\n" + "\n".join(errors)
                    raise ValidationError(error_message)