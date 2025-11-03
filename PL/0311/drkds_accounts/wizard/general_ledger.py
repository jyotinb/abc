from odoo import models, fields, api
import io
import base64
from datetime import datetime
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class GeneralLedgerWizard(models.TransientModel):
    _name = 'drkds.general.ledger.wizard'
    _description = 'General Ledger Report'
    
    date_from = fields.Date('From Date', required=True, default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    account_ids = fields.Many2many('account.account', string='Accounts')
    partner_ids = fields.Many2many('res.partner', string='Partners')
    journal_ids = fields.Many2many('account.journal', string='Journals')
    target_move = fields.Selection([('posted', 'Posted'), ('all', 'All')], default='posted', required=True)
    initial_balance = fields.Boolean('Include Initial Balance', default=True)
    
    def print_report(self):
        self.ensure_one()
        return self.env.ref('drkds_accounts.action_report_general_ledger').report_action(self, data=self._prepare_report_data())
    
    def _prepare_report_data(self):
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company_id.id,
            'account_ids': self.account_ids.ids,
            'partner_ids': self.partner_ids.ids,
            'journal_ids': self.journal_ids.ids,
            'target_move': self.target_move,
            'initial_balance': self.initial_balance,
        }
    
    def _get_account_move_lines(self):
        """Get all account move lines for the report"""
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]
        
        if self.target_move == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        
        return self.env['account.move.line'].search(domain, order='account_id, date, move_id')
    
    def _get_initial_balance(self, account_id):
        """Calculate initial balance for an account"""
        if not self.initial_balance:
            return 0.0
        
        domain = [
            ('date', '<', self.date_from),
            ('account_id', '=', account_id),
            ('company_id', '=', self.company_id.id),
        ]
        
        if self.target_move == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        
        lines = self.env['account.move.line'].search(domain)
        return sum(lines.mapped('debit')) - sum(lines.mapped('credit'))
    
    def _prepare_report_lines(self):
        """Prepare report lines grouped by account"""
        lines = self._get_account_move_lines()
        
        report_data = {}
        for line in lines:
            account = line.account_id
            if account.id not in report_data:
                report_data[account.id] = {
                    'account': account,
                    'initial_balance': self._get_initial_balance(account.id),
                    'lines': [],
                    'total_debit': 0.0,
                    'total_credit': 0.0,
                }
            
            report_data[account.id]['lines'].append(line)
            report_data[account.id]['total_debit'] += line.debit
            report_data[account.id]['total_credit'] += line.credit
        
        return report_data
    
    def export_excel(self):
        """Export General Ledger to Excel with full formatting"""
        self.ensure_one()
        
        # Create workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('General Ledger')
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center'
        })
        
        account_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E7E6E6',
            'border': 1
        })
        
        data_format = workbook.add_format({
            'border': 1,
            'align': 'left'
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
        
        # Set column widths
        worksheet.set_column('A:A', 12)  # Date
        worksheet.set_column('B:B', 15)  # Move
        worksheet.set_column('C:C', 15)  # Journal
        worksheet.set_column('D:D', 25)  # Account
        worksheet.set_column('E:E', 25)  # Partner
        worksheet.set_column('F:F', 35)  # Label
        worksheet.set_column('G:G', 15)  # Debit
        worksheet.set_column('H:H', 15)  # Credit
        worksheet.set_column('I:I', 15)  # Balance
        
        # Write title
        worksheet.merge_range('A1:I1', 'GENERAL LEDGER REPORT', title_format)
        worksheet.merge_range('A2:I2', f'{self.company_id.name}', title_format)
        worksheet.merge_range('A3:I3', f'Period: {self.date_from} to {self.date_to}', title_format)
        
        row = 4
        
        # Write headers
        headers = ['Date', 'Move', 'Journal', 'Account', 'Partner', 'Label', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        
        row += 1
        
        # Get report data
        report_data = self._prepare_report_lines()
        
        grand_total_debit = 0.0
        grand_total_credit = 0.0
        
        # Write data by account
        for account_id, data in sorted(report_data.items()):
            account = data['account']
            initial_balance = data['initial_balance']
            running_balance = initial_balance
            
            # Account header
            worksheet.merge_range(row, 0, row, 5, 
                                f"{account.code} - {account.name}", account_format)
            worksheet.write(row, 6, '', account_format)
            worksheet.write(row, 7, '', account_format)
            worksheet.write(row, 8, '', account_format)
            row += 1
            
            # Initial balance
            if self.initial_balance:
                worksheet.write(row, 0, '', data_format)
                worksheet.write(row, 1, '', data_format)
                worksheet.write(row, 2, '', data_format)
                worksheet.write(row, 3, '', data_format)
                worksheet.write(row, 4, '', data_format)
                worksheet.write(row, 5, 'Initial Balance', data_format)
                worksheet.write(row, 6, 0.0, number_format)
                worksheet.write(row, 7, 0.0, number_format)
                worksheet.write(row, 8, initial_balance, number_format)
                row += 1
            
            # Account lines
            for line in data['lines']:
                running_balance += line.debit - line.credit
                
                worksheet.write(row, 0, line.date.strftime('%Y-%m-%d') if line.date else '', data_format)
                worksheet.write(row, 1, line.move_id.name or '', data_format)
                worksheet.write(row, 2, line.journal_id.name or '', data_format)
                worksheet.write(row, 3, account.code or '', data_format)
                worksheet.write(row, 4, line.partner_id.name or '', data_format)
                worksheet.write(row, 5, line.name or '', data_format)
                worksheet.write(row, 6, line.debit, number_format)
                worksheet.write(row, 7, line.credit, number_format)
                worksheet.write(row, 8, running_balance, number_format)
                row += 1
            
            # Account total
            worksheet.write(row, 0, '', total_format)
            worksheet.write(row, 1, '', total_format)
            worksheet.write(row, 2, '', total_format)
            worksheet.write(row, 3, '', total_format)
            worksheet.write(row, 4, '', total_format)
            worksheet.write(row, 5, 'Total', total_format)
            worksheet.write(row, 6, data['total_debit'], total_format)
            worksheet.write(row, 7, data['total_credit'], total_format)
            worksheet.write(row, 8, running_balance, total_format)
            row += 2
            
            grand_total_debit += data['total_debit']
            grand_total_credit += data['total_credit']
        
        # Grand total
        worksheet.merge_range(row, 0, row, 5, 'GRAND TOTAL', total_format)
        worksheet.write(row, 6, grand_total_debit, total_format)
        worksheet.write(row, 7, grand_total_credit, total_format)
        worksheet.write(row, 8, grand_total_debit - grand_total_credit, total_format)
        
        workbook.close()
        
        # Create attachment
        excel_data = base64.b64encode(output.getvalue())
        filename = f'General_Ledger_{self.date_from}_{self.date_to}.xlsx'
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': excel_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
    def action_view_lines(self):
        """Open tree view of account move lines"""
        self.ensure_one()
        lines = self._get_account_move_lines()
        
        return {
            'name': 'General Ledger Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', lines.ids)],
            'context': {'create': False},
        }
