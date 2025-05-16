from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaymentSheetLine(models.Model):
    _name = 'payment.sheet.line'
    _description = 'Payment Sheet Line'
    
    payment_sheet_id = fields.Many2one('payment.sheet', string='Payment Sheet', 
                                      required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True,
                                domain=lambda self: [('id', 'in', self._get_partners_with_bank_accounts())])
    bank_account_id = fields.Many2one('bank.account', string='Bank Account', required=True,
                                     domain="[('partner_id', '=', partner_id), ('active', '=', True)]")
    account_name = fields.Char(related='bank_account_id.account_name', string='Account Name',
                              readonly=True, store=True)
    account_no = fields.Char(related='bank_account_id.account_no', string='Account Number',
                            readonly=True, store=True)
    ifsc_code = fields.Char(related='bank_account_id.ifsc_code', string='IFSC Code',
                           readonly=True, store=True)
    bank_name = fields.Char(related='bank_account_id.bank_name', string='Bank Name',
                           readonly=True, store=True)
    bank_id = fields.Many2one('res.bank', string='Bank (Structured)')
    email = fields.Char(related='bank_account_id.email', string='Email',
                       readonly=True, store=True)
    amount = fields.Float(string='Amount', required=True)
    instruction_reference = fields.Char(string='Instruction Reference Number',
                                      help="Reference number for banking instructions")
    customer_reference = fields.Char(string='Customer Reference Number',
                                   help="Customer reference number for payment tracking")
    remarks = fields.Text(string='Remarks')
    
    def _get_partners_with_bank_accounts(self):
        """Return partners who have bank accounts"""
        bank_accounts = self.env['bank.account'].search([('active', '=', True)])
        return bank_accounts.mapped('partner_id').ids
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.bank_account_id = False
        
    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(_("Amount must be greater than zero."))