from odoo import api, fields, models

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    top_parent_products = fields.Char(
        string='Top Parents',
        compute='_compute_top_parent_products',
        store=True
    )

    standard_price = fields.Float(
        string='Cost',
        related='product_id.standard_price',
        readonly=False,
        store=True
    )

    @api.onchange('standard_price')
    def _onchange_standard_price(self):
        if self.standard_price:
            return {
                # 'warning': {
                    # 'title': 'Warning!',
                    # 'message': 'This will update the cost in the product master data.'
                #}
            }

    def _get_all_top_parents(self, product, processed=None, depth=0):
        if processed is None:
            processed = set()
            
        if depth > 20:  # Prevent infinite loops
            return set()
            
        if not product or product.id in processed:
            return set()
            
        processed.add(product.id)
        top_parents = set()
        
        # Find all BOMs where this product is used as component
        parent_boms = self.env['mrp.bom'].search([
            ('bom_line_ids.product_id.product_tmpl_id', '=', product.id)
        ])
        
        if not parent_boms:
            top_parents.add(product.name)
        else:
            for bom in parent_boms:
                parent_product = bom.product_tmpl_id
                parent_tops = self._get_all_top_parents(parent_product, processed, depth + 1)
                top_parents.update(parent_tops)
                
        return top_parents

    @api.depends('bom_id', 'parent_product_tmpl_id')
    def _compute_top_parent_products(self):
        for line in self:
            # Start with direct parent's top parents
            all_top_parents = line._get_all_top_parents(line.parent_product_tmpl_id)
            
            if all_top_parents:
                line.top_parent_products = ', '.join(sorted(all_top_parents))
            else:
                line.top_parent_products = line.parent_product_tmpl_id.name
                
                

    @api.model
    def action_view_unique_components(self):
        # Get all components without sub-BOMs
        components = self.search([('product_id.product_tmpl_id.bom_ids', '=', False)])
        
        # Filter out duplicates, keeping only one record per product_id
        seen_products = set()
        unique_ids = []
        
        for comp in components:
            if comp.product_id.id not in seen_products:
                seen_products.add(comp.product_id.id)
                unique_ids.append(comp.id)
        
        # Return action
        return {
            'name': 'Unique BOM Components Without Sub BOM',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom.line',
            'view_mode': 'tree',
            'search_view_id': self.env.ref('drkds_rm_prices.view_bom_component_search').id,
            'domain': [('id', 'in', unique_ids)],
            'context': self.env.context,
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    No unique components found without sub BOMs
                </p>
                <p>
                    This view shows unique BOM components that don't have their own Bill of Materials.
                </p>
            """,
        }