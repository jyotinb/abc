from odoo import models, fields, api

class CreditLimit(models.Model):
    _name = 'drkds.credit.limit'
    _description = 'Credit Limit Management'
    
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    credit_limit = fields.Monetary('Credit Limit')
    credit_used = fields.Monetary('Credit Used', compute='_compute_credit_used')
    credit_available = fields.Monetary('Credit Available', compute='_compute_credit_available')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    @api.depends('partner_id')
    def _compute_credit_used(self):
        for rec in self:
            rec.credit_used = rec.partner_id.credit if rec.partner_id else 0.0
    
    @api.depends('credit_limit', 'credit_used')
    def _compute_credit_available(self):
        for rec in self:
            rec.credit_available = rec.credit_limit - rec.credit_used
