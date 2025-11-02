from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Ensuring we have access to the sale order information
    def _get_sale_order_number(self):
        """Get the sale order number related to this delivery"""
        for picking in self:
            if picking.origin:
                sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                if sale_order:
                    return sale_order.name
        return False
        
    def _get_total_gross_weight(self):
        """Calculate total gross weight of the picking including packaging.
        Takes into account loose_item_weight where applicable.
        """
        total_weight = 0.0
        
        # Get all packages used in this picking
        packages = self.env['stock.quant.package'].search([
            ('id', 'in', self.move_line_ids.mapped('result_package_id').ids)
        ])
        
        # Add weight from packaged items
        for package in packages:
            package_gw = 0.0
            
            # Check if any move lines associated with this package have loose_item_weight
            move_lines_with_loose_weight = self.move_line_ids.filtered(
                lambda l: l.result_package_id.id == package.id and 
                          hasattr(l, 'loose_item_weight') and 
                          l.loose_item_weight > 0
            )
            
            if move_lines_with_loose_weight:
                # If we have lines with loose_item_weight, use those values for the package
                for line in move_lines_with_loose_weight:
                    package_gw += line.loose_item_weight
            else:
                # Otherwise use the package weight
                package_gw = package.weight if package.weight > 0 else 0.0
            
            total_weight += package_gw
        
        # Add weight from unpacked items
        for move in self.move_ids:
            for line in move.move_line_ids.filtered(lambda l: not l.result_package_id):
                if hasattr(line, 'loose_item_weight') and line.loose_item_weight > 0:
                    total_weight += line.loose_item_weight
                else:
                    total_weight += line.product_id.weight * line.quantity
        
        return total_weight
        
    def _get_package_count(self):
        """Count the number of destination packages"""
        return len(self.move_line_ids.mapped('result_package_id'))
        
    def _get_product_packages(self, product_id):
        """Get the package names where this product is stored"""
        packages = self.move_line_ids.filtered(
            lambda l: l.product_id.id == product_id and l.result_package_id
        ).mapped('result_package_id.name')
        return ', '.join(packages) if packages else '-'
        
    def _get_packages_details(self):
        """
        Returns a list of dictionaries containing package details for the packing list report.
        Each dictionary contains: name, product_name, quantity, net_weight, gross_weight
        Takes into account loose_item_weight where applicable.
        """
        result = []
        
        # Get all packages used in this picking
        packages = self.env['stock.quant.package'].search([
            ('id', 'in', self.move_line_ids.mapped('result_package_id').ids)
        ])
        
        for package in packages:
            # Get package type base weight if available
            package_weight = 0.0
            if package.package_type_id and hasattr(package.package_type_id, 'base_weight'):
                package_weight = package.package_type_id.base_weight or 0.0
            
            # Get all move lines that use this package
            package_move_lines = self.move_line_ids.filtered(lambda ml: ml.result_package_id.id == package.id)
            
            # Group by product
            product_dict = {}
            for move_line in package_move_lines:
                product_id = move_line.product_id.id
                if product_id not in product_dict:
                    product_dict[product_id] = {
                        'product_id': product_id,
                        'product_name': move_line.product_id.name,
                        'quantity': 0,
                        'net_weight': 0.0,
                        'gross_weight': 0.0,
                        'has_loose_weight': False
                    }
                
                # Add quantity
                qty = move_line.quantity if move_line.quantity > 0 else move_line.product_uom_qty
                product_dict[product_id]['quantity'] += qty
                
                # Check for loose_item_weight
                if hasattr(move_line, 'loose_item_weight') and move_line.loose_item_weight > 0:
                    # If loose_item_weight is present, use it for calculations
                    product_dict[product_id]['has_loose_weight'] = True
                    product_dict[product_id]['gross_weight'] += move_line.loose_item_weight
                    product_dict[product_id]['net_weight'] += move_line.loose_item_weight - package_weight if package_weight else move_line.loose_item_weight
                else:
                    # Standard weight calculation
                    product_weight = move_line.product_id.weight or 0.0  # weight per unit in kg
                    product_dict[product_id]['net_weight'] += product_weight * qty
            
            # Create entry for each product in the package
            for product_data in product_dict.values():
                # If gross weight wasn't set by loose_item_weight, use package weight
                if not product_data['has_loose_weight']:
                    gross_weight = package.weight if package.weight > 0 else product_data['net_weight'] + package_weight
                else:
                    gross_weight = product_data['gross_weight']
                
                result.append({
                    'name': package.name or f'Package #{package.id}',
                    'product_name': product_data['product_name'],
                    'quantity': product_data['quantity'],
                    'net_weight': product_data['net_weight'],
                    'gross_weight': gross_weight
                })
        
        # If no packages are found, fallback to move lines without packages
        if not result:
            for move in self.move_ids:
                unpackaged_lines = move.move_line_ids.filtered(lambda l: not l.result_package_id)
                if unpackaged_lines:
                    qty = sum(line.quantity for line in unpackaged_lines)
                    
                    # Check for loose_item_weight in unpacked items
                    lines_with_loose_weight = unpackaged_lines.filtered(
                        lambda l: hasattr(l, 'loose_item_weight') and l.loose_item_weight > 0
                    )
                    
                    if lines_with_loose_weight:
                        # Use loose_item_weight for unpacked items
                        net_weight = sum(line.loose_item_weight for line in lines_with_loose_weight)
                        gross_weight = net_weight  # For unpacked items with loose_item_weight, GW = NW
                    else:
                        # Standard calculation for unpacked items
                        net_weight = (move.product_id.weight or 0.0) * qty
                        gross_weight = net_weight  # No packaging for unpacked items
                    
                    result.append({
                        'name': 'Unpacked',
                        'product_name': move.product_id.name,
                        'quantity': qty,
                        'net_weight': net_weight,
                        'gross_weight': gross_weight
                    })
        
        return result