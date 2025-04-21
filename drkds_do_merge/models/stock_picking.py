from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    merged_from_pickings = fields.Many2many(
        'stock.picking', 'stock_picking_merge_rel', 'merged_to_id', 'merged_from_id',
        string='Merged From', copy=False,
        help='Pickings that were merged into this one')
    
    merged_to_picking = fields.Many2many(
        'stock.picking', 'stock_picking_merge_rel', 'merged_from_id', 'merged_to_id',
        string='Merged Into', copy=False,
        help='Picking that this one was merged into')

    is_merged = fields.Boolean(
        string='Is Merged', compute='_compute_is_merged', store=True,
        help='Technical field to identify pickings that have been merged')

    original_sale_orders = fields.Many2many(
        'sale.order', string='Original Sales Orders',
        compute='_compute_original_sale_orders',
        help='All original sales orders related to this delivery')
        
    has_term_mismatches = fields.Boolean(
        string='Has Term Mismatches', compute='_compute_has_term_mismatches', store=True,
        help='Indicates that the merged delivery has orders with different terms')
        
    term_mismatch_notes = fields.Text(
        string='Term Mismatch Notes', 
        help='Notes about payment/delivery term mismatches')
    
    # Fields for selected terms
    selected_payment_term_id = fields.Many2one(
        'account.payment.term', string='Selected Payment Term',
        help='Payment term selected when merging delivery orders with different terms')
        
    selected_incoterm_id = fields.Many2one(
        'account.incoterms', string='Selected Delivery Term',
        help='Delivery term (incoterm) selected when merging delivery orders with different terms')

    @api.depends('merged_to_picking')
    def _compute_is_merged(self):
        for picking in self:
            picking.is_merged = bool(picking.merged_to_picking)

    @api.depends('move_ids.sale_line_id.order_id', 'merged_from_pickings.move_ids.sale_line_id.order_id')
    def _compute_original_sale_orders(self):
        for picking in self:
            sale_orders = picking.move_ids.mapped('sale_line_id.order_id')
            
            # Add sales orders from merged pickings
            for merged_picking in picking.merged_from_pickings:
                merged_sale_orders = merged_picking.move_ids.mapped('sale_line_id.order_id')
                sale_orders |= merged_sale_orders
                
            picking.original_sale_orders = sale_orders
            
    @api.depends('original_sale_orders')
    def _compute_has_term_mismatches(self):
        for picking in self:
            has_mismatches = False
            if len(picking.original_sale_orders) > 1:
                # Check payment terms
                payment_terms = picking.original_sale_orders.mapped('payment_term_id')
                if len(payment_terms) > 1:
                    has_mismatches = True
                
                # Check incoterms
                incoterms = picking.original_sale_orders.mapped('incoterm')
                if len(incoterms) > 1:
                    has_mismatches = True
                    
            picking.has_term_mismatches = has_mismatches
