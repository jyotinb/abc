# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)



class StockPicking(models.Model):
    _inherit = 'stock.picking'

   
    is_receipt = fields.Boolean(compute='_compute_is_receipt', string='Is Receipt')
    receipt = fields.Boolean(string='Receipt')
    is_subcontract_receipt = fields.Boolean(
        string='Is Subcontract Receipt',
        compute='_compute_is_subcontract_receipt',
        store=True
    )
    is_resupply = fields.Boolean(
        string='Is Resupply',
        compute='_compute_is_resupply',
        store=True
    )
    
    def button_test_compute(self):
        """Debug button to test compute methods"""
        self._compute_is_subcontract_receipt()
        self._compute_is_resupply()
    
    

    @api.depends('origin', 'picking_type_id', 'picking_type_id.code', 'name', 'state')
    def _compute_is_subcontract_receipt(self):
        for record in self:
            is_subcontract = False
            if record.picking_type_id.code == 'incoming' and record.origin:
                # Get the purchase order
                purchase_order = self.env['purchase.order'].search([
                    ('name', '=', record.origin)
                ], limit=1)
                
                if purchase_order:
                    # Check for resupply pickings that reference this receipt
                    resupply_pickings = self.env['stock.picking'].search([
                        ('origin', '=', record.name),
                        ('picking_type_id.name', 'ilike', 'Resupply')
                    ], limit=1)
                    
                    is_subcontract = bool(resupply_pickings)
            
            record.is_subcontract_receipt = is_subcontract


    @api.depends('origin', 'picking_type_id', 'picking_type_id.name')
    def _compute_is_resupply(self):
        for record in self:
            record.is_resupply = False
            if record.picking_type_id and record.picking_type_id.name:
                record.is_resupply = 'resupply' in record.picking_type_id.name.lower()

            

    # def _compute_is_receipt(self):
        # for rec in self:
            # is_receipt = False
            # if self.env.context.get('is_receipt'):
                # is_receipt = True
                # rec.receipt = True
            # rec.is_receipt = is_receipt

    

    # def button_validate(self):
        # res = super().button_validate()
        # context = self.env.context
        # purchase_order = self.env['purchase.order'].browse(context.get('active_id'))
    
        # for move in self.move_ids:
            # for picking in purchase_order.picking_ids:
                # receipt_move = picking.move_ids.filtered(lambda m: m.product_id.product_tmpl_id.id == move.bom_line_id.bom_id.product_tmpl_id.id)
                # receipt_move.delivered_weight = move.delivered_weight
                # receipt_move.delivered_weight_uom_id = move.delivered_weight_uom_id
        # return res



    def button_validate(self):
        res = super().button_validate()
        context = self.env.context
        
        # Check if active_id exists in context
        active_id = context.get('active_id')
        if not active_id:
            _logger.warning("Active ID not found in context.")
            return res
        
        # Browse the purchase order with the active ID
        purchase_order = self.env['purchase.order'].browse(active_id)
        
        # Ensure the purchase order exists
        if not purchase_order.exists():
            _logger.warning(f"Purchase order with ID {active_id} does not exist.")
            return res
        
        for move in self.move_ids:
            for picking in purchase_order.picking_ids:
                # Ensure the picking exists
                if not picking.exists():
                    _logger.warning(f"Picking record does not exist or has been deleted: {picking.id}")
                    continue
                
                # Filter receipt moves
                receipt_moves = picking.move_ids.filtered(
                    lambda m: m.product_id.product_tmpl_id.id == move.bom_line_id.bom_id.product_tmpl_id.id
                )
                
                # Ensure there are matching receipt moves
                if not receipt_moves:
                    _logger.warning(f"No matching receipt moves found for product template ID: {move.bom_line_id.bom_id.product_tmpl_id.id}")
                    continue
                
                try:
                    # Update the first matching move
                    receipt_move = receipt_moves[0]
                    receipt_move.delivered_weight = move.delivered_weight
                    receipt_move.delivered_weight_uom_id = move.delivered_weight_uom_id
                except Exception as e:
                    _logger.error(f"Error processing move {move.id}: {str(e)}")
        
        return res
