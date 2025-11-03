from odoo import models, fields, api

class RecurringEntry(models.Model):
    _name = 'drkds.recurring.entry'
    _description = 'Recurring Journal Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date')
    next_date = fields.Date('Next Date', required=True)
    recurring_period = fields.Selection([('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months'), ('years', 'Years')], required=True, default='months')
    recurring_interval = fields.Integer('Interval', required=True, default=1)
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running'), ('done', 'Done')], default='draft', tracking=True)
    line_ids = fields.One2many('drkds.recurring.entry.line', 'recurring_id', 'Lines')
    
    def action_start(self):
        self.write({'state': 'running'})
    
    def action_stop(self):
        self.write({'state': 'done'})
    
    def _generate_entries(self):
        pass  # Placeholder for cron

class RecurringEntryLine(models.Model):
    _name = 'drkds.recurring.entry.line'
    _description = 'Recurring Entry Line'
    
    recurring_id = fields.Many2one('drkds.recurring.entry', 'Recurring Entry', required=True, ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account', required=True)
    name = fields.Char('Label', required=True)
    debit = fields.Monetary('Debit', default=0.0)
    credit = fields.Monetary('Credit', default=0.0)
    partner_id = fields.Many2one('res.partner', 'Partner')
    currency_id = fields.Many2one('res.currency', related='recurring_id.company_id.currency_id')
