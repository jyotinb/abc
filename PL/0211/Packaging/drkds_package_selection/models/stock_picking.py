from odoo import models, fields, api, _
from lxml import etree

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def action_open_package_selection(self):
        """Open the package selection wizard"""
        self.ensure_one()
        
        # Only allow for delivery orders in appropriate states
        if self.picking_type_code != 'outgoing' or self.state not in ('assigned', 'partially_available'):
            return
        
        # Get available packages in the source location with relevant products
        domain = [
            ('location_id', 'child_of', self.location_id.id),
            ('package_id', '!=', False),
        ]
        
        # If we have move lines, filter by products in the delivery
        if self.move_line_ids:
            products = self.move_ids.mapped('product_id')
            if products:
                domain.append(('product_id', 'in', products.ids))
        
        available_packages = self.env['stock.quant'].search(domain).mapped('package_id')
        
        # Get packages that are already assigned to move lines
        assigned_packages = self.move_line_ids.filtered(
            lambda ml: ml.package_id and ml.state not in ('done', 'cancel')
        ).mapped('package_id')
        
        return {
            'name': _('Select Packages'),
            'type': 'ir.actions.act_window',
            'res_model': 'package.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_available_package_ids': [(6, 0, available_packages.ids)],
                'default_selected_package_ids': [(6, 0, assigned_packages.ids)],
            }
        }
    
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            # Customize package selection for move lines by adding display_name to the search results
            doc = etree.XML(result['arch'])
            package_nodes = doc.xpath("//field[@name='move_line_ids_without_package']/tree//field[@name='package_id']")
            if package_nodes:
                for node in package_nodes:
                    # Set options to display product info in dropdown
                    options = {
                        'no_create': True,
                        'no_open': False
                    }
                    node.set('options', str(options))
                    # Set a special field to display product names
                    node.set('context', "{'show_package_details': True}")
                result['arch'] = etree.tostring(doc, encoding='unicode')
        return result
        
        
        


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    package_product_names = fields.Char(
        string='Products in Package',
        compute='_compute_package_product_names',
        store=False
    )
    
    @api.depends('package_id', 'package_id.quant_ids')
    def _compute_package_product_names(self):
        for line in self:
            if not line.package_id or not line.package_id.quant_ids:
                line.package_product_names = ""
                continue
                
            product_names = line.package_id.quant_ids.mapped('product_id.name')
            if not product_names:
                line.package_product_names = ""
                continue
                
            if len(product_names) == 1:
                line.package_product_names = product_names[0]
            elif len(product_names) <= 3:
                line.package_product_names = ", ".join(product_names)
            else:
                line.package_product_names = f"{len(product_names)} different products"