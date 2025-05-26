from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_jobwork_order = fields.Boolean('Is Job Work', default=False)
    jobwork_receipt_count = fields.Integer(string='Job Work Receipts', compute='_compute_jobwork_receipt_count')
    jobwork_production_count = fields.Integer(string='Job Work MO', compute='_compute_jobwork_production_count')
    jobwork_delivery_count = fields.Integer(string='Job Work Deliveries', compute='_compute_jobwork_delivery_count')

   
    def _action_confirm(self):
        res = super()._action_confirm()  # This creates standard DO
        for order in self:
            if order.is_jobwork_order:
                # Get the standard created delivery order and update it
                pickings = self.env['stock.picking'].search([
                    ('sale_id', '=', order.id),
                    ('state', '=', 'draft'),
                    ('picking_type_code', '=', 'outgoing')
                ])
                if pickings:
                    pickings.write({
                        'is_job_work_delivery': True,
                        'jobwork_sale_id': self.id,
                    })
                
                jobwork_lines = order.order_line.filtered(lambda l: l.product_id.is_job_work)
                if jobwork_lines:
                    for line in jobwork_lines:
                        boms = self.env['mrp.bom']._bom_find(
                            products=line.product_id,
                            company_id=self.company_id.id,
                            picking_type=False
                        )
                        bom = boms[line.product_id]
                        if bom:
                            picking_in = self._create_jobwork_picking_in(line, bom)
                            mo = self._create_jobwork_manufacturing_order(line, picking_in, bom)
                            # Remove the _create_jobwork_picking_out call since we're using standard DO
                            
        return res


    
   

    # def _create_delivery_order(self):
        # # Skip if it's a job work order
        # if self._context.get('skip_delivery_creation'):
            # return True
        # return super()._create_delivery_order()
        
        
 


    def _create_jobwork_manufacturing_order(self, line, picking_in, bom):
        vals = {
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom_id': line.product_uom.id,
            'bom_id': bom.id,
            'origin': self.name,
            'jobwork_sale_id': self.id,
            'jobwork_picking_in_id': picking_in.id,
        }
        return self.env['mrp.production'].create(vals)

    # def _create_jobwork_picking_out(self, line, mo):
        # PickingType = self.env['stock.picking.type']
        # picking_type_out = PickingType.search([
            # ('code', '=', 'outgoing'),
            # ('warehouse_id.company_id', '=', self.company_id.id)
        # ], limit=1)
        
        # vals = {
            # 'partner_id': self.partner_id.id,
            # 'picking_type_id': picking_type_out.id,
            # 'location_id': picking_type_out.default_location_src_id.id,
            # 'location_dest_id': self.partner_id.property_stock_customer.id,
            # 'origin': self.name,
            # 'move_ids': [(0, 0, {
                # 'name': line.product_id.name,
                # 'product_id': line.product_id.id,
                # 'product_uom_qty': line.product_uom_qty,
                # 'product_uom': line.product_uom.id,
                # 'location_id': picking_type_out.default_location_src_id.id,
                # 'location_dest_id': self.partner_id.property_stock_customer.id,
            # })],
            # 'is_job_work_delivery': True,
            # 'jobwork_sale_id': self.id,
        # }
        # picking = self.env['stock.picking'].with_context(skip_purchase_validation=True).create(vals)
        # picking.action_confirm()
        # return picking
        
    def _create_jobwork_picking_out(self, line, mo):
        PickingType = self.env['stock.picking.type']
        
        # Fetch the outgoing picking type for the company
        picking_type_out = PickingType.search([
            ('code', '=', 'outgoing'),
            ('warehouse_id.company_id', '=', self.company_id.id)
        ], limit=1)

        if not picking_type_out:
            raise ValueError("No outgoing picking type found for the company.")

        # Fetch source and destination locations
        source_location = picking_type_out.default_location_src_id
        dest_location = self.partner_id.property_stock_customer

        if not source_location or not dest_location:
            raise ValueError("Source or Destination location is missing.")

        # Ensure required product data exists
        if not line.product_id or not line.product_uom_qty or not line.product_uom:
            raise ValueError("Missing product details in the line.")

        # Prepare picking values
        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_out.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'origin': self.name,
            'move_ids': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
            })],
            'is_job_work_delivery': True,
            'jobwork_sale_id': self.id,
        }

        # Create picking with context to skip purchase validation
        picking = self.env['stock.picking'].with_context(skip_purchase_validation=True).create(picking_vals)

        # Confirm the picking to start processing
        picking.action_confirm()

        return picking
    
   
    def _compute_jobwork_receipt_count(self):
        for order in self:
            pickings = self.env['stock.picking'].search_count([
                ('origin', '=', order.name),
                ('is_job_work_receipt', '=', True)
            ])
            order.jobwork_receipt_count = pickings

    def action_view_jobwork_receipts(self):
        self.ensure_one()
        pickings = self.env['stock.picking'].search([
            ('origin', '=', self.name),
            ('is_job_work_receipt', '=', True)
        ])
        action = {
            'name': _('Job Work Receipts'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', pickings.ids)],
            'context': {'default_is_job_work_receipt': True}
        }
        if len(pickings) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': pickings.id,
            })
        return action

    def _create_jobwork_picking_in(self, line, bom):
        PickingType = self.env['stock.picking.type']
        picking_type_in = PickingType.search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', self.company_id.id)
        ], limit=1)
        
        move_lines = []
        for component in bom.bom_line_ids:
            move_lines.append((0, 0, {
                'name': component.product_id.name,
                'product_id': component.product_id.id,
                'product_uom_qty': component.product_qty * line.product_uom_qty / bom.product_qty,
                'product_uom': component.product_uom_id.id,  # Changed from product_uom to product_uom_id
                'location_id': self.partner_id.property_stock_customer.id,
                'location_dest_id': picking_type_in.default_location_dest_id.id,
            }))
        
        vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_in.id,
            'location_id': self.partner_id.property_stock_customer.id,
            'location_dest_id': picking_type_in.default_location_dest_id.id,
            'origin': self.name,
            'move_ids': move_lines,
            'is_job_work_receipt': True,
            'jobwork_sale_id': self.id,
        }
        
        picking = self.env['stock.picking'].with_context(skip_purchase_validation=True).create(vals)
        picking.action_confirm()
        return picking
        
 

    def _compute_jobwork_production_count(self):
        for order in self:
            productions = self.env['mrp.production'].search([
                ('jobwork_sale_id', '=', order.id)
            ])
            order.jobwork_production_count = len(productions)



    def action_view_jobwork_productions(self):
        self.ensure_one()
        productions = self.env['mrp.production'].search([
            ('jobwork_sale_id', '=', self.id)
        ])
        action = {
            'name': _('Job Work Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', productions.ids)],
            'context': {'default_jobwork_sale_id': self.id}
        }
        if len(productions) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': productions.id,
            })
        return action
        
 
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id')
    def _compute_is_mto(self):
        super()._compute_is_mto()
        for line in self:
            if line.order_id.is_jobwork_order:
                line.is_mto = False

    # def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        # if self.order_id.is_jobwork_order:
            # return True
        # return super()._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty) 
        
        
        
class StockMove(models.Model):
    _inherit = 'stock.move'

    jobwork_sale_id = fields.Many2one('sale.order', 'Job Work Sale Order')        


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    jobwork_sale_id = fields.Many2one('sale.order', 'Job Work Sale Order')
    jobwork_picking_in_id = fields.Many2one('stock.picking', 'Raw Material Receipt')
    jobwork_picking_out_id = fields.Many2one('stock.picking', 'Finished Goods Delivery')
    is_jobwork = fields.Boolean('Is Job Work', related='jobwork_sale_id.is_jobwork_order')

