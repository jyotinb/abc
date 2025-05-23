# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Simple variant functionality
    apply_on_variants = fields.Boolean(
        'Apply on Variants',
        default=False,
        help="If checked, this BOM will only be used for the selected product variants."
    )
    
    product_variant_ids = fields.Many2many(
        'product.product',
        'mrp_bom_product_variant_rel',
        'bom_id',
        'product_id',
        string='Product Variants',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help="Select which product variants this BOM applies to."
    )

    @api.onchange('apply_on_variants')
    def _onchange_apply_on_variants(self):
        if not self.apply_on_variants:
            self.product_variant_ids = False

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        if hasattr(super(MrpBom, self), '_onchange_product_tmpl_id'):
            res = super()._onchange_product_tmpl_id()
        else:
            res = {}
        if self.product_tmpl_id:
            self.product_variant_ids = False
        return res

    @api.constrains('apply_on_variants', 'product_variant_ids', 'product_id')
    def _check_variant_consistency(self):
        for bom in self:
            if bom.apply_on_variants and not bom.product_variant_ids:
                raise ValidationError(_(
                    "When 'Apply on Variants' is enabled, you must select at least one product variant."
                ))
            
            if bom.product_id and bom.apply_on_variants:
                raise ValidationError(_(
                    "You cannot use both 'Product Variant' and 'Apply on Variants' at the same time. "
                    "Please choose one method."
                ))

    @api.model
    def _bom_find(self, products, picking_type=None, company_id=False, bom_type=False):
        """Enhanced BOM finding with variant support"""
        result = super()._bom_find(products, picking_type, company_id, bom_type)
        
        # Look for variant-specific BOMs
        for product in products:
            if product in result:
                continue
                
            # Search for BOMs that apply to this specific variant
            variant_boms = self.search([
                ('apply_on_variants', '=', True),
                ('product_variant_ids', 'in', product.ids),
                ('active', '=', True),
                ('product_tmpl_id', '=', product.product_tmpl_id.id)
            ], limit=1, order='sequence, id')
            
            if variant_boms:
                result[product] = variant_boms
        
        return result
