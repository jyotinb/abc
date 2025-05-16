from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BankAccount(models.Model):
    _name = 'bank.account'
    _description = 'Bank Account Details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'account_name'
    
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True,
                                 domain=[])
    account_name = fields.Char(string='Account Name', required=True, tracking=True)
    account_no = fields.Char(string='Account Number', required=True, tracking=True)
    ifsc_code = fields.Char(string='IFSC Code', required=True, tracking=True)
    bank_name = fields.Char(string='Bank Name', required=True, tracking=True)  # Added bank name
    bank_id = fields.Many2one('res.bank', string='Bank ')
    email = fields.Char(string='Bank Email', tracking=True)  # Added email field
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    _sql_constraints = [
        ('account_no_unique', 'unique(account_no)', 'The account number must be unique!')
    ]
    
    @api.constrains('account_no')
    def _check_account_no(self):
        for record in self:
            if not record.account_no.isalnum():
                raise ValidationError(_("Account number should contain only alphanumeric characters."))
    
    @api.constrains('ifsc_code')
    def _check_ifsc_code(self):
        for record in self:
            if not record.ifsc_code or len(record.ifsc_code) != 11:
                raise ValidationError(_("IFSC Code must be 11 characters long."))
            if not record.ifsc_code.isalnum():
                raise ValidationError(_("IFSC Code should contain only alphanumeric characters."))