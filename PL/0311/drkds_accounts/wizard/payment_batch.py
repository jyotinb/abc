from odoo import models, fields

class PaymentBatchWizard(models.TransientModel):
    _name = 'drkds.payment.batch.wizard'
    _description = 'Create Payment Batch'
    
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money')
    ], required=True, default='outbound')
    payment_date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    
    def action_create_payment_order(self):
        return {'type': 'ir.actions.act_window_close'}
