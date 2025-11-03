from odoo import models, fields

class LockDate(models.Model):
    _name = 'drkds.lock.date'
    _description = 'Period Lock'
    
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    lock_date = fields.Date('Lock Date', required=True)
    user_ids = fields.Many2many('res.users', string='Users Allowed to Post')
    active = fields.Boolean(default=True)

class FiscalYear(models.Model):
    _name = 'drkds.fiscal.year'
    _description = 'Fiscal Year'
    
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    state = fields.Selection([('draft', 'Open'), ('closed', 'Closed')], default='draft')
