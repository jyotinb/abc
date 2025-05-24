# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class BomVariantApplyWizardAttributeLine(models.TransientModel):
    _name = 'drkds.bom.variant.apply.wizard.line'
    _description = 'BoM Variant Apply Wizard Line'
    
    wizard_id = fields.Many2one(
        'drkds.bom.variant.apply.wizard', 
        string='Wizard', 
        required=True, 
        ondelete='cascade'
    )
    attribute_id = fields.Many2one(
        'product.attribute', 
        string='Attribute', 
        required=True
    )
    value_ids = fields.Many2many(
        'product.template.attribute.value',
        string='Values',
        domain="[('attribute_id', '=', attribute_id), ('product_tmpl_id', '=', parent.product_tmpl_id)]"
    )
    
    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        if self.attribute_id:
            # Reset values when attribute changes
            self.value_ids = False

class BomVariantApplyWizard(models.TransientModel):
    _name = 'drkds.bom.variant.apply.wizard'
    _description = 'Apply BoM on Variants Wizard'
    
    bom_id = fields.Many2one(
        'mrp.bom', 
        string='Bill of Material', 
        required=True
    )
    bom_line_id = fields.Many2one(
        'mrp.bom.line', 
        string='BoM Line', 
        required=True
    )
    product_tmpl_id = fields.Many2one(
        'product.template', 
        string='Product Template', 
        required=True
    )
    attribute_line_ids = fields.One2many(
        'drkds.bom.variant.apply.wizard.line', 
        'wizard_id', 
        string='Attributes'
    )
    current_attributes = fields.Text(
        'Current Attribute Values', 
        compute='_compute_current_attributes'
    )
    
    @api.depends('bom_line_id')
    def _compute_current_attributes(self):
        for wizard in self:
            if not wizard.bom_line_id or not wizard.bom_line_id.bom_product_template_attribute_value_ids:
                wizard.current_attributes = _("No variant restrictions currently applied.")
            else:
                values = wizard.bom_line_id.bom_product_template_attribute_value_ids
                attrs = {}
                for value in values:
                    attr_name = value.attribute_id.name
                    if attr_name not in attrs:
                        attrs[attr_name] = []
                    attrs[attr_name].append(value.name)
                
                result = []
                for attr, vals in attrs.items():
                    result.append(f"{attr}: {', '.join(vals)}")
                
                wizard.current_attributes = "\n".join(result)
    
    def action_apply(self):
        """Apply the selected variant restrictions to the BoM line"""
        self.ensure_one()
        
        # Collect all selected attribute values
        attribute_value_ids = []
        for line in self.attribute_line_ids:
            if line.value_ids:
                attribute_value_ids.extend(line.value_ids.ids)
        
        if not attribute_value_ids:
            # If no values selected, remove all restrictions
            return self.action_remove()
        
        # Apply the restrictions
        self.bom_id.apply_variant_restriction(self.bom_line_id.id, attribute_value_ids)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Variant restrictions applied successfully.'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_remove(self):
        """Remove all variant restrictions from the BoM line"""
        self.ensure_one()
        
        # Remove the restrictions
        self.bom_id.remove_variant_restriction(self.bom_line_id.id)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Variant restrictions removed successfully.'),
                'sticky': False,
                'type': 'success',
            }
        }
