from odoo import models, fields, api

class PaymentOrder(models.Model):
    _name = 'drkds.payment.order'
    _description = 'Payment Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Reference', required=True, copy=False, default='New')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    payment_mode_id = fields.Many2one('drkds.payment.mode', 'Payment Mode')
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], required=True, default='outbound')
    payment_date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done')], default='draft', tracking=True)
    line_ids = fields.One2many('drkds.payment.order.line', 'order_id', 'Payment Lines')
    total_amount = fields.Monetary('Total Amount', compute='_compute_total', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    @api.depends('line_ids.amount')
    def _compute_total(self):
        for order in self:
            order.total_amount = sum(order.line_ids.mapped('amount'))
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})

class PaymentOrderLine(models.Model):
    _name = 'drkds.payment.order.line'
    _description = 'Payment Order Line'
    
    order_id = fields.Many2one('drkds.payment.order', 'Payment Order', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    amount = fields.Monetary('Amount', required=True)
    communication = fields.Char('Communication')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id')

class PaymentMode(models.Model):
    _name = 'drkds.payment.mode'
    _description = 'Payment Mode'
    
    name = fields.Char('Name', required=True)
    bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    active = fields.Boolean(default=True)
