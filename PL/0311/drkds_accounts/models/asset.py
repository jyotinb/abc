from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class Asset(models.Model):
    _name = 'drkds.asset'
    _description = 'Asset Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'purchase_date desc, code'
    
    name = fields.Char('Asset Name', required=True, tracking=True, index=True)
    code = fields.Char('Reference', required=True, copy=False, default='New', index=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    
    category_id = fields.Many2one('drkds.asset.category', 'Asset Category', tracking=True)
    purchase_date = fields.Date('Purchase Date', required=True, default=fields.Date.today, tracking=True)
    purchase_value = fields.Monetary('Purchase Value', required=True, tracking=True)
    salvage_value = fields.Monetary('Salvage Value', default=0.0, tracking=True)
    
    method = fields.Selection([
        ('linear', 'Linear'),
        ('degressive', 'Degressive'),
        ('accelerated', 'Accelerated')
    ], string='Computation Method', required=True, default='linear', tracking=True)
    method_number = fields.Integer('Number of Depreciations', default=5, required=True)
    method_period = fields.Selection([
        ('1', 'Monthly'),
        ('3', 'Quarterly'),
        ('12', 'Yearly')
    ], string='Period Length', required=True, default='12')
    method_progress_factor = fields.Float('Degressive Factor', default=0.3)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Running'),
        ('close', 'Closed')
    ], default='draft', tracking=True, copy=False)
    
    active = fields.Boolean(default=True)
    depreciation_line_ids = fields.One2many('drkds.asset.depreciation', 'asset_id', 'Depreciation Lines')
    value_residual = fields.Monetary('Residual Value', compute='_compute_residual_value', store=True)
    value_depreciated = fields.Monetary('Depreciated Value', compute='_compute_residual_value', store=True)
    
    account_asset_id = fields.Many2one('account.account', 'Asset Account')
    account_depreciation_id = fields.Many2one('account.account', 'Depreciation Account')
    account_depreciation_expense_id = fields.Many2one('account.account', 'Expense Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    
    partner_id = fields.Many2one('res.partner', 'Vendor')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    location = fields.Char('Location')
    serial_number = fields.Char('Serial Number')
    notes = fields.Text('Notes')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('drkds.asset') or 'AST' + str(self.env['drkds.asset'].search_count([]) + 1).zfill(5)
        return super().create(vals_list)
    
    @api.depends('depreciation_line_ids.amount', 'depreciation_line_ids.move_posted_check')
    def _compute_residual_value(self):
        for asset in self:
            posted_lines = asset.depreciation_line_ids.filtered('move_posted_check')
            asset.value_depreciated = sum(posted_lines.mapped('amount'))
            asset.value_residual = asset.purchase_value - asset.value_depreciated
    
    def compute_depreciation_board(self):
        self.ensure_one()
        
        # Remove old draft lines
        self.depreciation_line_ids.filtered(lambda l: not l.move_posted_check).unlink()
        
        if self.purchase_value <= self.salvage_value:
            raise ValidationError('Purchase value must be greater than salvage value!')
        
        amount_to_depr = self.purchase_value - self.salvage_value
        residual_amount = amount_to_depr
        depreciation_date = self.purchase_date
        
        for i in range(1, self.method_number + 1):
            # Calculate depreciation amount
            if self.method == 'linear':
                amount = amount_to_depr / self.method_number
            elif self.method == 'degressive':
                amount = residual_amount * self.method_progress_factor
            else:  # accelerated
                amount = residual_amount * (2.0 / self.method_number)
            
            # Last depreciation
            if i == self.method_number or amount > residual_amount:
                amount = residual_amount
            
            depreciation_date = depreciation_date + relativedelta(months=int(self.method_period))
            
            self.env['drkds.asset.depreciation'].create({
                'asset_id': self.id,
                'sequence': i,
                'amount': amount,
                'depreciation_date': depreciation_date,
                'remaining_value': residual_amount - amount,
            })
            
            residual_amount -= amount
            
            if residual_amount < 0.01:
                break
        
        return True
    
    def action_validate(self):
        self.ensure_one()
        
        if not self.account_asset_id or not self.account_depreciation_id or not self.account_depreciation_expense_id:
            raise UserError('Please configure all required accounts!')
        
        if not self.journal_id:
            raise UserError('Please select a journal!')
        
        self.compute_depreciation_board()
        self.write({'state': 'open'})
        
        return True
    
    def action_close(self):
        self.write({'state': 'close', 'active': False})
        return True
    
    def action_draft(self):
        if self.depreciation_line_ids.filtered('move_posted_check'):
            raise UserError('Cannot reset to draft - depreciation entries already posted!')
        self.write({'state': 'draft'})
        return True

class AssetCategory(models.Model):
    _name = 'drkds.asset.category'
    _description = 'Asset Category'
    _order = 'name'
    
    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True)
    account_asset_id = fields.Many2one('account.account', 'Asset Account')
    account_depreciation_id = fields.Many2one('account.account', 'Depreciation Account')
    account_depreciation_expense_id = fields.Many2one('account.account', 'Expense Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    method_number = fields.Integer('Number of Depreciations', default=5)
    method_period = fields.Selection([
        ('1', 'Monthly'), 
        ('3', 'Quarterly'), 
        ('12', 'Yearly')
    ], default='12', string='Period Length')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    notes = fields.Text('Notes')

class AssetDepreciation(models.Model):
    _name = 'drkds.asset.depreciation'
    _description = 'Asset Depreciation Line'
    _order = 'asset_id, sequence'
    
    asset_id = fields.Many2one('drkds.asset', 'Asset', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Depreciation Name', compute='_compute_name', store=True)
    amount = fields.Monetary('Amount')
    depreciation_date = fields.Date('Date')
    remaining_value = fields.Monetary('Remaining Value')
    
    move_id = fields.Many2one('account.move', 'Journal Entry')
    move_posted_check = fields.Boolean('Posted', compute='_compute_move_posted_check', store=True)
    
    currency_id = fields.Many2one('res.currency', related='asset_id.currency_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', related='asset_id.company_id', store=True, readonly=True)
    
    @api.depends('asset_id', 'sequence')
    def _compute_name(self):
        for line in self:
            if line.asset_id and line.sequence:
                line.name = f"{line.asset_id.name} - {line.sequence}/{line.asset_id.method_number}"
            else:
                line.name = 'Depreciation'
    
    @api.depends('move_id.state')
    def _compute_move_posted_check(self):
        for line in self:
            line.move_posted_check = line.move_id and line.move_id.state == 'posted'
    
    def create_move(self):
        self.ensure_one()
        
        if self.move_id:
            return self.move_id
        
        if not self.asset_id.account_depreciation_expense_id or not self.asset_id.account_depreciation_id:
            raise UserError('Please configure depreciation accounts!')
        
        move_vals = {
            'journal_id': self.asset_id.journal_id.id,
            'date': self.depreciation_date,
            'ref': self.name,
            'asset_id': self.asset_id.id,
            'line_ids': [
                (0, 0, {
                    'name': self.name,
                    'account_id': self.asset_id.account_depreciation_expense_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': self.name,
                    'account_id': self.asset_id.account_depreciation_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                })
            ]
        }
        
        move = self.env['account.move'].create(move_vals)
        self.write({'move_id': move.id})
        
        return move
    
    def post_move(self):
        for line in self:
            if not line.move_id:
                line.create_move()
            
            if line.move_id.state == 'draft':
                line.move_id.action_post()
        
        return True
