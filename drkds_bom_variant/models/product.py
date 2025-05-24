# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    variant_bom_count = fields.Integer(
        'Variant BoM Count', 
        compute='_compute_variant_bom_count'
    )
    has_variant_bom = fields.Boolean(
        'Has Variant BoM', 
        compute='_compute_has_variant_bom',
        store=True
    )
    
    @api.depends('product_tmpl_id.bom_ids')
    def _compute_variant_bom_count(self):
        for product in self:
            product.variant_bom_count = self.env['mrp.bom'].search_count([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_id', '=', product.id)
            ])
    
    @api.depends('product_tmpl_id.bom_ids')
    def _compute_has_variant_bom(self):
        for product in self:
            product.has_variant_bom = bool(self.env['mrp.bom'].search_count([
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('product_id', '=', product.id)
            ]))
    
    def action_view_variant_boms(self):
        """View variant-specific BoMs for this product"""
        self.ensure_one()
        boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('product_id', '=', self.id)
        ])
        
        action = self.env.ref('mrp.mrp_bom_form_action').read()[0]
        if len(boms) == 1:
            action['views'] = [(self.env.ref('mrp.mrp_bom_form_view').id, 'form')]
            action['res_id'] = boms.id
        else:
            action['domain'] = [('id', 'in', boms.ids)]
        
        return action
    
    def action_create_variant_bom(self):
        """Create a variant-specific BoM for this product"""
        self.ensure_one()
        
        # Find a template BoM to use as a basis
        template_bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
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
        variant_bom = template_bom.create_variant_bom(self.id)
        
        # Open the new BoM
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': variant_bom.id,
            'view_mode': 'form',
            'target': 'current',
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    variant_bom_count = fields.Integer(
        'Variant BoM Count', 
        compute='_compute_variant_bom_count'
    )
    
    @api.depends('bom_ids')
    def _compute_variant_bom_count(self):
        for template in self:
            template.variant_bom_count = self.env['mrp.bom'].search_count([
                ('product_tmpl_id', '=', template.id),
                ('product_id', '!=', False)
            ])
    
    def action_view_variant_boms(self):
        """View all variant-specific BoMs for this product template"""
        self.ensure_one()
        boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.id),
            ('product_id', '!=', False)
        ])
        
        action = self.env.ref('mrp.mrp_bom_form_action').read()[0]
        action['domain'] = [('id', 'in', boms.ids)]
        action['context'] = {
            'default_product_tmpl_id': self.id,
        }
        
        return action