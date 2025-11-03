from odoo import models, fields, api
import io
import base64
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class TrialBalanceWizard(models.TransientModel):
    _name = 'drkds.trial.balance.wizard'
    _description = 'Trial Balance Report'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    target_move = fields.Selection([('posted', 'Posted'), ('all', 'All')], default='posted', required=True)
    display_accounts = fields.Selection([
        ('all', 'All Accounts'),
        ('movement', 'With Movements'),
        ('balance', 'With Balance')
    ], default='movement', required=True)
    hierarchy = fields.Boolean('Show Hierarchy', default=False)
    
    def _get_accounts_data(self):
        """Get account balances for the period"""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('deprecated', '=', False),
        ]
        
        accounts = self.env['account.account'].search(domain, order='code')
        
        account_data = {}
        for account in accounts:
            # Get opening balance (before date_from)
            opening_domain = [
                ('account_id', '=', account.id),
                ('date', '<', self.date_from),
                ('company_id', '=', self.company_id.id),
            ]
            if self.target_move == 'posted':
                opening_domain.append(('parent_state', '=', 'posted'))
            
            opening_lines = self.env['account.move.line'].search(opening_domain)
            opening_debit = sum(opening_lines.mapped('debit'))
            opening_credit = sum(opening_lines.mapped('credit'))
            opening_balance = opening_debit - opening_credit
            
            # Get period movements
            period_domain = [
                ('account_id', '=', account.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('company_id', '=', self.company_id.id),
            ]
            if self.target_move == 'posted':
                period_domain.append(('parent_state', '=', 'posted'))
            
            period_lines = self.env['account.move.line'].search(period_domain)
            period_debit = sum(period_lines.mapped('debit'))
            period_credit = sum(period_lines.mapped('credit'))
            
            # Calculate closing balance
            closing_balance = opening_balance + period_debit - period_credit
            
            # Apply display filter
            has_movement = period_debit != 0 or period_credit != 0
            has_balance = closing_balance != 0
            
            if self.display_accounts == 'movement' and not has_movement:
                continue
            if self.display_accounts == 'balance' and not has_balance:
                continue
            
            account_data[account.id] = {
                'account': account,
                'opening_balance': opening_balance,
                'period_debit': period_debit,
                'period_credit': period_credit,
                'closing_balance': closing_balance,
            }
        
        return account_data
    
    def print_report(self):
        self.ensure_one()
        account_data = self._get_accounts_data()
        
        # Here you would pass data to QWeb report
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Trial Balance',
                'message': f'Report generated with {len(account_data)} accounts',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def export_excel(self):
        """Export Trial Balance to Excel"""
        self.ensure_one()
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Trial Balance')
        
        # Formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'bg_color': '#4472C4',
            'font_color': 'white'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00'
        })
        
        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '#,##0.00',
            'bg_color': '#F2F2F2'
        })
        
        # Column widths
        worksheet.set_column('A:A', 12)  # Code
        worksheet.set_column('B:B', 35)  # Account Name
        worksheet.set_column('C:C', 15)  # Opening Balance
        worksheet.set_column('D:D', 15)  # Debit
        worksheet.set_column('E:E', 15)  # Credit
        worksheet.set_column('F:F', 15)  # Closing Balance
        
        # Title
        worksheet.merge_range('A1:F1', 'TRIAL BALANCE', title_format)
        worksheet.merge_range('A2:F2', f'{self.company_id.name}', title_format)
        worksheet.merge_range('A3:F3', f'Period: {self.date_from} to {self.date_to}', title_format)
        
        row = 4
        
        # Headers
        headers = ['Code', 'Account Name', 'Opening Balance', 'Debit', 'Credit', 'Closing Balance']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        
        row += 1
        
        # Get data
        account_data = self._get_accounts_data()
        
        total_opening = 0.0
        total_debit = 0.0
        total_credit = 0.0
        total_closing = 0.0
        
        # Write account lines
        for acc_id, data in sorted(account_data.items(), key=lambda x: x[1]['account'].code):
            account = data['account']
            
            worksheet.write(row, 0, account.code or '', {'border': 1})
            worksheet.write(row, 1, account.name or '', {'border': 1})
            worksheet.write(row, 2, data['opening_balance'], number_format)
            worksheet.write(row, 3, data['period_debit'], number_format)
            worksheet.write(row, 4, data['period_credit'], number_format)
            worksheet.write(row, 5, data['closing_balance'], number_format)
            
            total_opening += data['opening_balance']
            total_debit += data['period_debit']
            total_credit += data['period_credit']
            total_closing += data['closing_balance']
            
            row += 1
        
        # Total row
        worksheet.write(row, 0, '', total_format)
        worksheet.write(row, 1, 'TOTAL', total_format)
        worksheet.write(row, 2, total_opening, total_format)
        worksheet.write(row, 3, total_debit, total_format)
        worksheet.write(row, 4, total_credit, total_format)
        worksheet.write(row, 5, total_closing, total_format)
        
        # Verification
        row += 2
        worksheet.write(row, 1, 'Verification:', {'bold': True})
        row += 1
        worksheet.write(row, 1, 'Total Debit = Total Credit:')
        worksheet.write(row, 2, 'OK' if abs(total_debit - total_credit) < 0.01 else 'ERROR', 
                       {'bold': True, 'font_color': 'green' if abs(total_debit - total_credit) < 0.01 else 'red'})
        
        workbook.close()
        
        excel_data = base64.b64encode(output.getvalue())
        filename = f'Trial_Balance_{self.date_from}_{self.date_to}.xlsx'
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': excel_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
