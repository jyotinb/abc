from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_job_work_receipt = fields.Boolean('Is Job Work Receipt', default=False)
    is_job_work_delivery = fields.Boolean('Is Job Work Delivery', default=False)
    customer_dc = fields.Char('Customer DC No')
    customer_dc_date = fields.Date('DC Date')
    jobwork_sale_id = fields.Many2one('sale.order', 'Job Work Order')

    def _action_done(self):
        for picking in self:
            
            if picking.is_job_work_receipt or picking.is_job_work_delivery:
                
                picking = picking.with_context(skip_purchase_validation=True)
        return super(StockPicking, self)._action_done()

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self):
        
        moves_to_skip = self.env['stock.move']
        for move in self:
            if move.picking_id and (move.picking_id.is_job_work_receipt or move.picking_id.is_job_work_delivery):
                moves_to_skip |= move
        
        if moves_to_skip:
            
            return super(StockMove, moves_to_skip.with_context(skip_purchase_validation=True))._action_assign()
        return super()._action_assign()

    def _action_done(self, cancel_backorder=False):
        moves_to_skip = self.env['stock.move']
        # if not self:
            # raise UserError("No pickings found!")
        for move in self:
            
            if move.picking_id and (move.picking_id.is_job_work_receipt or move.picking_id.is_job_work_delivery):
                moves_to_skip |= move
        
        if moves_to_skip:
            
            return super(StockMove, moves_to_skip.with_context(skip_purchase_validation=True))._action_done(cancel_backorder=cancel_backorder)
        #raise UserError("No pickings found!")
        return super(StockMove, self.with_context(skip_purchase_validation=True))._action_done(cancel_backorder=cancel_backorder)
        #return super()._action_done(cancel_backorder=cancel_backorder)
    
    


    def _get_price_unit(self):
        self.ensure_one()
        if self.picking_id and (self.picking_id.is_job_work_receipt or self.picking_id.is_job_work_delivery):
            return 0.0
        return super()._get_price_unit()