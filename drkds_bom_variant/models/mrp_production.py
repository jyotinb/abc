# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    is_variant_specific = fields.Boolean(
        'Variant Specific', 
        compute='_compute_is_variant_specific', 
        store=True
    )
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
    
    @api.depends('product_id', 'bom_id')
    def _compute_is_variant_specific(self):
        for production in self:
            production.is_variant_specific = (
                production.product_id and 
                production.bom_id and 
                production.bom_id.product_id == production.product_id
            )
    
    @api.depends('product_id', 'bom_id')
    def _compute_has_variant_bom(self):
        for production in self:
            variant_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', production.product_id.product_tmpl_id.id),
                ('product_id', '=', production.product_id.id)
            ], limit=1)
            production.has_variant_bom = bool(variant_bom)
    
    @api.depends('product_id')
    def _compute_variant_bom_id(self):
        for production in self:
            if not production.product_id:
                production.variant_bom_id = False
                continue
                
            variant_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', production.product_id.product_tmpl_id.id),
                ('product_id', '=', production.product_id.id)
            ], limit=1)
            production.variant_bom_id = variant_bom
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(MrpProduction, self)._onchange_product_id()
        
        # If a variant-specific BoM exists, use it
        if self.product_id:
            variant_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('product_id', '=', self.product_id.id)
            ], limit=1)
            
            if variant_bom:
                self.bom_id = variant_bom
                # Trigger onchange for bom_id to update lines
                self._onchange_bom_id()
                _logger.info(
                    "Using variant-specific BoM %s for production of %s", 
                    variant_bom.display_name, self.product_id.display_name
                )
        
        return res
    
    def action_create_variant_bom(self):
        """Create a variant-specific BoM for this manufacturing order"""
        self.ensure_one()
        
        if not self.product_id or not self.bom_id:
            raise UserError(_("Cannot create variant BoM without a product and BoM."))
        
        if self.is_variant_specific:
            raise UserError(_("This manufacturing order already uses a variant-specific BoM."))
        
        # Check if template BoM has variant management enabled
        if not self.bom_id.variant_management_enabled:
            # Enable it automatically
            self.bom_id.variant_management_enabled = True
            _logger.info("Enabled variant management for BoM %s", self.bom_id.display_name)
        
        # Create the variant BoM
        variant_bom = self.bom_id.create_variant_bom(self.product_id.id)
        
        # Update the manufacturing order
        self.bom_id = variant_bom.id
        self._onchange_bom_id()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Variant BoM Created'),
                'message': _('A variant-specific BoM has been created and applied to this manufacturing order.'),
                'sticky': False,
                'type': 'success',
            }
        }
    
    @api.model
    def _prepare_mo_vals(self, sale_line, product_qty):
        """Override to use variant-specific BoM if available"""
        vals = super(MrpProduction, self)._prepare_mo_vals(sale_line, product_qty)
        
        # Check if a variant-specific BoM exists for this product
        if sale_line.product_id:
            variant_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', sale_line.product_id.product_tmpl_id.id),
                ('product_id', '=', sale_line.product_id.id)
            ], limit=1)
            
            if variant_bom:
                vals['bom_id'] = variant_bom.id
                _logger.info(
                    "Using variant-specific BoM %s for SO line %s", 
                    variant_bom.display_name, sale_line.display_name
                )
        
        return vals
