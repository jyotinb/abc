from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PackageSelectionWizard(models.TransientModel):
    _name = 'package.selection.wizard'
    _description = 'Package Selection Wizard'
    
    picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery Order',
        required=True
    )
    
    available_package_ids = fields.Many2many(
        'stock.quant.package',
        'package_selection_avail_rel',
        'wizard_id',
        'package_id',
        string='Available Packages',
        help='All packages available in the source location'
    )
    
    selected_package_ids = fields.Many2many(
        'stock.quant.package',
        'package_selection_selected_rel',
        'wizard_id',
        'package_id',
        string='Selected Packages',
        domain="[('id', 'in', available_package_ids)]"
    )
    
    total_selected_qty = fields.Float(
        string='Total Selected Quantity',
        compute='_compute_total_selected_qty'
    )
    
    @api.depends('selected_package_ids', 'selected_package_ids.total_qty')
    def _compute_total_selected_qty(self):
        for wizard in self:
            wizard.total_selected_qty = sum(wizard.selected_package_ids.mapped('total_qty'))
    
    def action_confirm(self):
        """Apply selected packages to the delivery order"""
        self.ensure_one()
        
        if not self.selected_package_ids:
            raise UserError(_("Please select at least one package."))
        
        picking = self.picking_id
        
        # Clear existing move lines that are not done
        picking.move_line_ids.filtered(lambda ml: ml.state not in ('done', 'cancel')).unlink()
        
        # Create move lines for each product in the selected packages
        package_quants = self.env['stock.quant'].search([
            ('package_id', 'in', self.selected_package_ids.ids),
            ('location_id', 'child_of', picking.location_id.id),
        ])
        
        move_lines_values = []
        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            product_quants = package_quants.filtered(lambda q: q.product_id == move.product_id)
            
            if not product_quants:
                continue
                
            for quant in product_quants:
                move_lines_values.append({
                    'move_id': move.id,
                    'product_id': quant.product_id.id,
                    'product_uom_id': quant.product_id.uom_id.id,
                    'location_id': quant.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'package_id': quant.package_id.id,
                    'result_package_id': quant.package_id.id,
                    'lot_id': quant.lot_id.id if quant.lot_id else False,
                    'quantity': quant.quantity,
                    'picking_id': picking.id,
                })
        
        if move_lines_values:
            self.env['stock.move.line'].create(move_lines_values)
            picking.message_post(body=_("Move lines created from selected packages."))
        else:
            raise UserError(_("No matching products found in the selected packages."))
        
        return {'type': 'ir.actions.act_window_close'}