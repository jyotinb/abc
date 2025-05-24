# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class DrkdsBomVariantLog(models.Model):
    _name = 'drkds.bom.variant.log'
    _description = 'BoM Variant Log'
    _order = 'create_date desc'

    name = fields.Char('Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    bom_id = fields.Many2one('mrp.bom', 'Bill of Material', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product Variant', required=True)
    user_id = fields.Many2one('res.users', 'User', required=True, default=lambda self: self.env.user)
    action = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('apply', 'Apply Variant'),
        ('remove', 'Remove Variant'),
    ], string='Action', required=True)
    description = fields.Text('Description')
    attribute_values = fields.Text('Attribute Values')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('drkds.bom.variant.log') or _('New')
        return super(DrkdsBomVariantLog, self).create(vals_list)

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    variant_management_enabled = fields.Boolean(
        'Enable Variant Management', 
        help="Enable this to manage BoMs specific to product variants"
    )
    variant_specific = fields.Boolean(
        'Variant Specific', 
        compute='_compute_variant_specific', 
        store=True,
        help="This BoM is specific to a product variant"
    )
    variant_log_ids = fields.One2many(
        'drkds.bom.variant.log', 
        'bom_id', 
        string='Variant Logs'
    )
    parent_bom_id = fields.Many2one(
        'mrp.bom', 
        string='Parent BoM',
        help="Reference to the parent BoM from which this variant-specific BoM was created"
    )
    child_bom_ids = fields.One2many(
        'mrp.bom', 
        'parent_bom_id', 
        string='Variant BoMs',
        help="Variant-specific BoMs created from this template BoM"
    )
    variant_count = fields.Integer(
        'Variant Count', 
        compute='_compute_variant_count'
    )
    
    @api.depends('bom_line_ids.bom_product_template_attribute_value_ids', 'product_id')
    def _compute_variant_specific(self):
        for bom in self:
            if bom.product_id:
                bom.variant_specific = True
            elif bom.bom_line_ids.filtered(lambda l: l.bom_product_template_attribute_value_ids):
                bom.variant_specific = True
            else:
                bom.variant_specific = False
    
    @api.depends('child_bom_ids')
    def _compute_variant_count(self):
        for bom in self:
            bom.variant_count = len(bom.child_bom_ids)
    
    def action_view_variants(self):
        self.ensure_one()
        return {
            'name': _('Variant BoMs'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'mrp.bom',
            'domain': [('parent_bom_id', '=', self.id)],
            'context': {'default_parent_bom_id': self.id}
        }
    
    def _create_variant_log(self, product, action, description=False, attribute_values=False):
        """Create a log entry for variant BoM operations"""
        self.ensure_one()
        values = {
            'bom_id': self.id,
            'product_id': product.id,
            'action': action,
            'description': description or '',
        }
        
        if attribute_values:
            if isinstance(attribute_values, list):
                values['attribute_values'] = ", ".join([av.name for av in attribute_values])
            else:
                values['attribute_values'] = attribute_values
                
        log = self.env['drkds.bom.variant.log'].create(values)
        _logger.info(
            'BoM Variant Log created: %s for BoM %s, Product %s, Action %s', 
            log.name, self.display_name, product.display_name, action
        )
        return log
    
    def create_variant_bom(self, product_id, copy_lines=True):
        """Create a variant-specific BoM based on this template BoM"""
        self.ensure_one()
        
        if not self.variant_management_enabled:
            raise UserError(_("Variant management is not enabled for this BoM."))
        
        product = self.env['product.product'].browse(product_id)
        if not product or product.product_tmpl_id != self.product_tmpl_id:
            raise ValidationError(_("The product variant must belong to the same product template."))
        
        # Check if a variant BoM already exists
        existing_bom = self.env['mrp.bom'].search([
            ('product_id', '=', product_id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('parent_bom_id', '=', self.id)
        ], limit=1)
        
        if existing_bom:
            return existing_bom
        
        vals = {
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_id': product_id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'type': self.type,
            'code': f"{self.code or self.product_tmpl_id.name}-{product.display_name}",
            'parent_bom_id': self.id,
            'variant_management_enabled': True,
        }
        
        new_bom = self.env['mrp.bom'].create(vals)
        
        # Copy BoM lines if requested
        if copy_lines:
            for line in self.bom_line_ids:
                # Skip lines that have variant restrictions that don't match
                if line.bom_product_template_attribute_value_ids:
                    if not all(value in product.product_template_attribute_value_ids for value in line.bom_product_template_attribute_value_ids):
                        continue
                
                line_vals = {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom_id.id,
                    'sequence': line.sequence,
                    'bom_id': new_bom.id,
                }
                self.env['mrp.bom.line'].create(line_vals)
        
        # Log the creation
        attribute_values = product.product_template_attribute_value_ids
        self._create_variant_log(
            product=product,
            action='create',
            description=f"Created variant BoM for {product.display_name}",
            attribute_values=attribute_values
        )
        
        _logger.info("Created variant BoM %s for product %s", new_bom.display_name, product.display_name)
        return new_bom
    
    def apply_variant_restriction(self, line_id, attribute_value_ids):
        """Apply variant restrictions to a BoM line"""
        self.ensure_one()
        
        if not self.variant_management_enabled:
            raise UserError(_("Variant management is not enabled for this BoM."))
        
        line = self.env['mrp.bom.line'].browse(line_id)
        if not line or line.bom_id != self:
            raise ValidationError(_("Invalid BoM line."))
        
        attribute_values = self.env['product.template.attribute.value'].browse(attribute_value_ids)
        if not attribute_values:
            raise ValidationError(_("No attribute values specified."))
        
        # Verify attribute values belong to the product template
        for value in attribute_values:
            if value.product_tmpl_id != self.product_tmpl_id:
                raise ValidationError(_(
                    "The attribute value %s does not belong to product %s.",
                    value.display_name, self.product_tmpl_id.display_name
                ))
        
        # Apply restriction
        line.bom_product_template_attribute_value_ids = [(6, 0, attribute_value_ids)]
        
        # Get a representative product for logging
        domain = [
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('product_template_attribute_value_ids', 'in', attribute_value_ids)
        ]
        product = self.env['product.product'].search(domain, limit=1)
        
        # Log the change
        self._create_variant_log(
            product=product or self.product_tmpl_id.product_variant_ids[0],
            action='apply',
            description=f"Applied variant restriction to line {line.product_id.display_name}",
            attribute_values=attribute_values
        )
        
        _logger.info(
            "Applied variant restriction to BoM %s, line %s with values %s", 
            self.display_name, line.product_id.display_name, 
            ", ".join([av.name for av in attribute_values])
        )
        return True
    
    def remove_variant_restriction(self, line_id):
        """Remove variant restrictions from a BoM line"""
        self.ensure_one()
        
        line = self.env['mrp.bom.line'].browse(line_id)
        if not line or line.bom_id != self:
            raise ValidationError(_("Invalid BoM line."))
        
        if not line.bom_product_template_attribute_value_ids:
            return True
        
        # Get data for logging before removal
        attribute_values = line.bom_product_template_attribute_value_ids
        
        # Get a representative product for logging
        domain = [
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('product_template_attribute_value_ids', 'in', attribute_values.ids)
        ]
        product = self.env['product.product'].search(domain, limit=1)
        
        # Remove restriction
        line.bom_product_template_attribute_value_ids = [(5, 0, 0)]
        
        # Log the change
        self._create_variant_log(
            product=product or self.product_tmpl_id.product_variant_ids[0],
            action='remove',
            description=f"Removed variant restriction from line {line.product_id.display_name}",
            attribute_values=", ".join([av.name for av in attribute_values])
        )
        
        _logger.info(
            "Removed variant restriction from BoM %s, line %s", 
            self.display_name, line.product_id.display_name
        )
        return True


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    is_variant_specific = fields.Boolean(
        'Variant Specific', 
        compute='_compute_is_variant_specific', 
        store=True
    )
    
    @api.depends('bom_product_template_attribute_value_ids')
    def _compute_is_variant_specific(self):
        for line in self:
            line.is_variant_specific = bool(line.bom_product_template_attribute_value_ids)
    
    def action_open_variant_wizard(self):
        """Open the wizard to apply variant restrictions"""
        self.ensure_one()
        
        wizard = self.env['drkds.bom.variant.apply.wizard'].create({
            'bom_id': self.bom_id.id,
            'bom_line_id': self.id,
            'product_tmpl_id': self.bom_id.product_tmpl_id.id,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': line.attribute_id.id,
            }) for line in self.bom_id.product_tmpl_id.attribute_line_ids],
        })
        
        # Set current values if any
        if self.bom_product_template_attribute_value_ids:
            for wiz_line in wizard.attribute_line_ids:
                for value in self.bom_product_template_attribute_value_ids:
                    if value.attribute_id == wiz_line.attribute_id:
                        wiz_line.value_ids = [(4, value.id)]
        
        return {
            'name': _('Apply on Variants'),
            'type': 'ir.actions.act_window',
            'res_model': 'drkds.bom.variant.apply.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
