# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    has_variant_bom = fields.Boolean(
        'Has Variant BoM', 
        compute='_compute_has_variant_bom',
        store=True
    )
    variant_bom_id = fields.Many2one(
        'mrp.bom', 
        string='Variant BoM',
        compute='_compute_variant_bom_id',
        store=True
    )
    
    @api.depends('product_id')
    def _compute_has_variant_bom(self):
        for line in self:
            if not line.product_id:
                line.has_variant_bom = False
                continue
                
            variant_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('product_id', '=', line.product_id.id)
            ], limit=1)
            line.has_variant_bom = bool(variant_bom)
    
    @api.depends('product_id')
    def _compute_variant_bom_id(self):
        for line in self:
            if not line.product_id:
                line.variant_bom_id = False
                continue
                
            variant_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('product_id', '=', line.product_id.id)
            ], limit=1)
            line.variant_bom_id = variant_bom
    
    def action_view_variant_bom(self):
        """View the variant-specific BoM for this sale line"""
        self.ensure_one()
        
        if not self.variant_bom_id:
            raise UserError(_("No variant-specific BoM found for this product."))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': self.variant_bom_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_create_variant_bom(self):
        """Create a variant-specific BoM for this sale line's product"""
        self.ensure_one()
        
        if not self.product_id:
            raise UserError(_("Cannot create a variant BoM without a product."))
        
        if self.has_variant_bom:
            return self.action_view_variant_bom()
        
        # Find a template BoM to use as a basis
        template_bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('product_id', '=', False)
        ], limit=1)
        
        if not template_bom:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Template BoM'),
                    'message': _('No template BoM found for this product. Please create a template BoM first.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Enable variant management if not already enabled
        if not template_bom.variant_management_enabled:
            template_bom.variant_management_enabled = True
            _logger.info("Enabled variant management for BoM %s", template_bom.display_name)
        
        # Create the variant BoM
        variant_bom = template_bom.create_variant_bom(self.product_id.id)
        
        # Update computed fields
        self._compute_has_variant_bom()
        self._compute_variant_bom_id()
        
        # Open the new BoM
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': variant_bom.id,
            'view_mode': 'form',
            'target': 'current',
        }
