from odoo import models, fields

class BudgetReportWizard(models.TransientModel):
    _name = 'drkds.budget.report.wizard'
    _description = 'Budget Analysis Report'
    
    date_from = fields.Date('From Date', required=True)
    date_to = fields.Date('To Date', required=True)
    budget_ids = fields.Many2many('drkds.budget', string='Budgets')
    
    def print_report(self):
        return {'type': 'ir.actions.act_window_close'}
