from odoo import models, fields, api

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'
    
    total_qty = fields.Float(
        string='Total Quantity',
        compute='_compute_total_qty',
        store=True
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    product_names = fields.Char(
        string='Products',
        compute='_compute_product_names',
        store=True
    )
    
    @api.depends('quant_ids', 'quant_ids.quantity')
    def _compute_total_qty(self):
        for package in self:
            package.total_qty = sum(package.quant_ids.mapped('quantity'))
    
    @api.depends('name', 'total_qty')
    def _compute_display_name(self):
        for package in self:
            product_name = "Product"  # Default product name placeholder
            if package.quant_ids and package.quant_ids.mapped('product_id.name'):
                product_names = package.quant_ids.mapped('product_id.name')
                product_name = product_names[0] if len(product_names) == 1 else f"{len(product_names)} products"
            
            package.display_name = f"{package.name} ({product_name})({package.total_qty:.1f})"
    
    @api.depends('quant_ids', 'quant_ids.product_id')
    def _compute_product_names(self):
        for package in self:
            if not package.quant_ids:
                package.product_names = ""
                continue
                
            product_names = package.quant_ids.mapped('product_id.name')
            if not product_names:
                package.product_names = ""
                continue
                
            if len(product_names) == 1:
                package.product_names = product_names[0]
            elif len(product_names) <= 3:
                package.product_names = ", ".join(product_names)
            else:
                package.product_names = f"{len(product_names)} different products"
    
    def name_get(self):
        """Override name_get to show product information in dropdowns"""
        result = []
        for package in self:
            # Check if we should show package details
            show_details = self.env.context.get('show_package_details', False)
            
            if show_details:
                # Show with product details
                if package.product_names:
                    name = f"{package.name} ({package.product_names})"
                else:
                    name = package.name
            else:
                name = package.name
                
            result.append((package.id, name))
        return result