from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Budget(models.Model):
    _name = 'drkds.budget'
    _description = 'Budget Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, name'
    
    name = fields.Char('Budget Name', required=True, tracking=True)
    code = fields.Char('Code', required=True, copy=False)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date('Start Date', required=True, tracking=True)
    date_to = fields.Date('End Date', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('validated', 'Validated'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True, copy=False)
    
    budget_line_ids = fields.One2many('drkds.budget.line', 'budget_id', 'Budget Lines', copy=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    
    planned_amount = fields.Monetary('Planned Amount', compute='_compute_amounts', store=True)
    practical_amount = fields.Monetary('Practical Amount', compute='_compute_amounts', store=True)
    theoretical_amount = fields.Monetary('Theoretical Amount', compute='_compute_amounts', store=True)
    percentage = fields.Float('Achievement %', compute='_compute_amounts', store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    
    notes = fields.Text('Notes')
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    alert_threshold = fields.Float('Alert Threshold %', default=90.0)
    
    @api.depends('budget_line_ids.planned_amount', 'budget_line_ids.practical_amount', 
                 'budget_line_ids.theoretical_amount')
    def _compute_amounts(self):
        for budget in self:
            budget.planned_amount = sum(budget.budget_line_ids.mapped('planned_amount'))
            budget.practical_amount = sum(budget.budget_line_ids.mapped('practical_amount'))
            budget.theoretical_amount = sum(budget.budget_line_ids.mapped('theoretical_amount'))
            if budget.planned_amount:
                budget.percentage = (budget.practical_amount / budget.planned_amount) * 100
            else:
                budget.percentage = 0.0
            
            # Check alert threshold
            if budget.state == 'validated' and budget.percentage > budget.alert_threshold:
                budget.message_post(
                    body=f"⚠️ Budget alert: {budget.percentage:.1f}% utilized (threshold: {budget.alert_threshold}%)",
                    subject="Budget Threshold Exceeded"
                )
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for budget in self:
            if budget.date_from and budget.date_to and budget.date_from > budget.date_to:
                raise ValidationError('End date must be after start date!')
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
        return True
    
    def action_validate(self):
        # Validate budget lines have valid data
        for line in self.budget_line_ids:
            if line.planned_amount <= 0:
                raise ValidationError(f'Planned amount must be positive for line: {line.analytic_account_id.name}')
        
        self.write({'state': 'validated'})
        return True
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True
    
    def action_draft(self):
        self.write({'state': 'draft'})
        return True
    
    def action_done(self):
        self.write({'state': 'done'})
        return True
    
    def action_refresh_practical(self):
        """Manually refresh practical amounts from actual data"""
        for line in self.budget_line_ids:
            line._compute_practical_amount()
        return True

class BudgetLine(models.Model):
    _name = 'drkds.budget.line'
    _description = 'Budget Line'
    _order = 'date_from'
    
    budget_id = fields.Many2one('drkds.budget', 'Budget', required=True, ondelete='cascade', index=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    general_account_id = fields.Many2one('account.account', 'General Account')
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    
    planned_amount = fields.Monetary('Planned Amount', required=True)
    practical_amount = fields.Monetary('Practical Amount', compute='_compute_practical_amount', store=True)
    theoretical_amount = fields.Monetary('Theoretical Amount', compute='_compute_theoretical_amount', store=True)
    percentage = fields.Float('Achievement %', compute='_compute_percentage', store=True)
    
    company_id = fields.Many2one(related='budget_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    
    paid_date = fields.Date('Paid Date')
    notes = fields.Char('Notes')
    
    @api.depends('analytic_account_id', 'general_account_id', 'date_from', 'date_to')
    def _compute_practical_amount(self):
        """Calculate actual amount spent from analytic lines"""
        for line in self:
            if not line.analytic_account_id:
                line.practical_amount = 0.0
                continue
            
            domain = [
                ('date', '>=', line.date_from),
                ('date', '<=', line.date_to),
                ('account_id', '=', line.analytic_account_id.id),
            ]
            
            if line.general_account_id:
                domain.append(('general_account_id', '=', line.general_account_id.id))
            
            # Get analytic lines
            analytic_lines = self.env['account.analytic.line'].search(domain)
            
            # Sum amounts (negative for expenses, positive for revenue)
            line.practical_amount = abs(sum(analytic_lines.mapped('amount')))
    
    @api.depends('date_from', 'date_to', 'planned_amount')
    def _compute_theoretical_amount(self):
        """Calculate theoretical amount based on elapsed time"""
        today = fields.Date.today()
        for line in self:
            if not line.date_from or not line.date_to:
                line.theoretical_amount = 0.0
                continue
            
            total_days = (line.date_to - line.date_from).days + 1
            
            if line.date_from <= today <= line.date_to:
                # Period in progress
                elapsed_days = (today - line.date_from).days + 1
                line.theoretical_amount = (line.planned_amount / total_days) * elapsed_days
            elif today > line.date_to:
                # Period ended
                line.theoretical_amount = line.planned_amount
            else:
                # Period not started
                line.theoretical_amount = 0.0
    
    @api.depends('planned_amount', 'practical_amount')
    def _compute_percentage(self):
        for line in self:
            if line.planned_amount:
                line.percentage = (line.practical_amount / line.planned_amount) * 100
            else:
                line.percentage = 0.0
    
    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for line in self:
            if line.date_from and line.date_to and line.date_from > line.date_to:
                raise ValidationError('End date must be after start date!')
    
    @api.constrains('planned_amount')
    def _check_planned_amount(self):
        for line in self:
            if line.planned_amount < 0:
                raise ValidationError('Planned amount cannot be negative!')
