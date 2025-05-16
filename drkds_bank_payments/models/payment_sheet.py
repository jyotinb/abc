from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
#import xlsxwriter
import xlwt
import io
from datetime import datetime


class PaymentSheet(models.Model):
    _name = 'payment.sheet'
    _description = 'Payment Sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, 
                       default=lambda self: _('New'))
    date = fields.Date(string='Date', required=True, tracking=True, 
                     default=fields.Date.context_today)
    payment_line_ids = fields.One2many('payment.sheet.line', 'payment_sheet_id', 
                                     string='Payment Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid')
    ], string='Status', default='draft', tracking=True)
    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_count')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    remarks = fields.Text(string='Remarks', tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('payment.sheet') or _('New')
        return super(PaymentSheet, self).create(vals_list)
    
    @api.depends('payment_line_ids')
    def _compute_payment_count(self):
        for sheet in self:
            sheet.payment_count = len(sheet.payment_line_ids)
    
    @api.depends('payment_line_ids.amount')
    def _compute_total_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.payment_line_ids.mapped('amount'))
    
    def action_confirm(self):
        for sheet in self:
            if not sheet.payment_line_ids:
                raise UserError(_("You cannot confirm a payment sheet with no payment lines."))
            sheet.write({'state': 'confirmed'})
    
    def action_mark_paid(self):
        for sheet in self:
            if sheet.state != 'confirmed':
                raise UserError(_("Only confirmed payment sheets can be marked as paid."))
            sheet.write({'state': 'paid'})
    
    def action_reset_to_draft(self):
        for sheet in self:
            if not self.env.user.has_group('drkds_bank_payments.group_bank_payment_manager'):
                raise UserError(_("Only managers can reset payment sheets to draft status."))
            sheet.write({'state': 'draft'})
    
    def create_new_line(self):
        """
        Function to add a new payment line from the form view button
        """
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("You can only add lines to draft payment sheets."))
            
        context = {
            'default_payment_sheet_id': self.id,
        }
        return {
            'name': _('Add Payment Line'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'payment.sheet.line',
            'target': 'new',
            'context': context,
        }
    
    # def action_export_excel(self):
        # """
        # Export the payment sheet data to Excel with bank-specific headers and custom mapping
        # """
        # self.ensure_one()
        # if not self.payment_line_ids:
            # return {
                # 'type': 'ir.actions.client',
                # 'tag': 'display_notification',
                # 'params': {
                    # 'title': _('No Data'),
                    # 'message': _('No payment lines to export.'),
                    # 'sticky': False,
                # }
            # }
        
        # # Create Excel file
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output)
        # worksheet = workbook.add_worksheet('Payment Sheet')
        
        # # Define styles
        # header_style = workbook.add_format({
            # 'bold': True, 
            # 'align': 'center', 
            # 'valign': 'vcenter',
            # 'bg_color': '#4472C4',
            # 'font_color': 'white',
            # 'border': 1
        # })
        
        # cell_style = workbook.add_format({
            # 'align': 'left',
            # 'border': 1
        # })
        
        # amount_style = workbook.add_format({
            # 'num_format': '#,##0.00',
            # 'align': 'right',
            # 'border': 1
        # })
        
        # date_style = workbook.add_format({
            # 'num_format': 'dd/mm/yyyy',
            # 'align': 'center',
            # 'border': 1
        # })
        
        # # Write headers as required by the bank format
        # headers = [
            # 'Transaction Type',
            # 'Beneficiary Code',
            # 'Beneficiary Account Number',
            # 'Instrument Amount',
            # 'Beneficiary Name',
            # 'Drawee Location',
            # 'Print Location',
            # 'Bene Address 1',
            # 'Bene Address 2',
            # 'Bene Address 3',
            # 'Bene Address 4',
            # 'Bene Address 5',
            # 'Instruction Reference Number',
            # 'Customer Reference Number',
            # 'Payment details 1',
            # 'Payment details 2',
            # 'Payment details 3',
            # 'Payment details 4',
            # 'Payment details 5',
            # 'Payment details 6',
            # 'Payment details 7',
            # 'Cheque Number',
            # 'Chq / Trn Date',
            # 'MICR Number',
            # 'IFC Code',
            # 'Bene Bank Name',
            # 'Bene Bank Branch Name',
            # 'Beneficiary email id'
        # ]
        
        # for col, header in enumerate(headers):
            # worksheet.write(0, col, header, header_style)
        
        # # Write payment line data
        # row = 1
        # for line in self.payment_line_ids:
            # # Transaction Type based on bank and amount
            # if line.bank_account_id and line.bank_account_id.bank_name and isinstance(line.bank_account_id.bank_name, str):
                # transaction_type = 'I' if line.bank_account_id.bank_name.startswith('HDFC') else ('N' if line.amount < 200000 else 'R')
            # else:
                # # Default value when bank_name is not available or not a string
                # transaction_type = 'N' if line.amount < 200000 else 'R'
            
            # # Column 0: Transaction Type
            # worksheet.write(row, 0, transaction_type, cell_style)
            
            # # Column 1: Beneficiary Code fixed as 'AGROTCX'
            # worksheet.write(row, 1, 'AGROTCX', cell_style)
            
            # # Column 2: Beneficiary Account Number
            # worksheet.write(row, 2, line.account_no, cell_style)
            
            # # Column 3: Instrument Amount
            # worksheet.write(row, 3, line.amount, amount_style)
            
            # # Column 4: Beneficiary Name
            # worksheet.write(row, 4, line.partner_id.name, cell_style)
            
            # # Columns 5-6: Drawee Location and Print Location (leave blank)
            # worksheet.write(row, 5, '', cell_style)  # Drawee Location
            # worksheet.write(row, 6, '', cell_style)  # Print Location
            
            # # Columns 7-11: Beneficiary Address fields (leave blank)
            # for col in range(7, 12):
                # worksheet.write(row, col, '', cell_style)
            
            # # Column 12-13: Reference Numbers
            # worksheet.write(row, 12, line.instruction_reference or '', cell_style)  # Instruction Reference Number
            # worksheet.write(row, 13, line.customer_reference or '', cell_style)  # Customer Reference Number
            
            # # Columns 14-20: Payment details fields (leave blank)
            # for col in range(14, 21):
                # worksheet.write(row, col, '', cell_style)
            
            # # Column 21: Cheque Number (leave blank)
            # worksheet.write(row, 21, '', cell_style)
            
            # # Column 22: Chq / Trn Date
            # worksheet.write(row, 22, ',' + self.date.strftime('%d/%m/%Y'), cell_style)
            
            # # Column 23: MICR Number (leave blank)
            # worksheet.write(row, 23, '', cell_style)
            
            # # Column 24: IFC Code
            # worksheet.write(row, 24, line.ifsc_code, cell_style)
            
            # # Column 25: Bene Bank Name
            # worksheet.write(row, 25, line.bank_name, cell_style)
            
            # # Column 26: Bene Bank Branch Name (leave blank)
            # worksheet.write(row, 26, '', cell_style)
            
            # # Column 27: Beneficiary email id
            # worksheet.write(row, 27, line.email or '', cell_style)
            
            # row += 1
        
        # # Adjust column widths for better readability
        # column_widths = {
            # 0: 15,   # Transaction Type
            # 1: 15,   # Beneficiary Code
            # 2: 25,   # Beneficiary Account Number
            # 3: 15,   # Instrument Amount
            # 4: 25,   # Beneficiary Name
            # 5: 15,   # Drawee Location
            # 6: 15,   # Print Location
            # 7: 20,   # Bene Address 1
            # 8: 20,   # Bene Address 2
            # 9: 20,   # Bene Address 3
            # 10: 20,  # Bene Address 4
            # 11: 20,  # Bene Address 5
            # 12: 25,  # Instruction Reference Number
            # 13: 25,  # Customer Reference Number
            # 14: 20,  # Payment details 1
            # 15: 20,  # Payment details 2
            # 16: 20,  # Payment details 3
            # 17: 20,  # Payment details 4
            # 18: 20,  # Payment details 5
            # 19: 20,  # Payment details 6
            # 20: 20,  # Payment details 7
            # 21: 15,  # Cheque Number
            # 22: 15,  # Chq / Trn Date
            # 23: 15,  # MICR Number
            # 24: 15,  # IFC Code
            # 25: 20,  # Bene Bank Name
            # 26: 20,  # Bene Bank Branch Name
            # 27: 30,  # Beneficiary email id
        # }
        
        # for col, width in column_widths.items():
            # worksheet.set_column(col, col, width)
        
        # workbook.close()
        # output.seek(0)
        
        # # Create attachment
        # filename = f"Payment_Sheet_{self.name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        # attachment_vals = {
            # 'name': filename,
            # 'datas': base64.b64encode(output.read()),
            # 'res_model': 'payment.sheet',
            # 'res_id': self.id,
            # 'type': 'binary',
        # }
        # attachment = self.env['ir.attachment'].create(attachment_vals)
        
        # # Return download action
        # return {
            # 'type': 'ir.actions.act_url',
            # 'url': f'/web/content/{attachment.id}?download=true',
            # 'target': 'self',
        # }
        
        
 

    def action_export_excel(self):
        """
        Export the payment sheet data to XLS with bank-specific headers and custom mapping
        """
        self.ensure_one()

        if not self.payment_line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Data'),
                    'message': _('No payment lines to export.'),
                    'sticky': False,
                }
            }

        # Create workbook and sheet
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Payment Sheet')

        # Define styles
        header_style = xlwt.easyxf(
            'font: bold on, color white; '
            'align: horiz center; '
            'pattern: pattern solid, fore_color blue; '
            'borders: left thin, right thin, top thin, bottom thin'
        )

        cell_style = xlwt.easyxf(
            'align: horiz left; '
            'borders: left thin, right thin, top thin, bottom thin'
        )

        amount_style = xlwt.easyxf(
            'align: horiz right; '
            'borders: left thin, right thin, top thin, bottom thin',
            num_format_str='#,##0.00'
        )

        date_style = xlwt.easyxf(
            'align: horiz center; '
            'borders: left thin, right thin, top thin, bottom thin',
            num_format_str='DD/MM/YYYY'
        )

        # Define headers
        headers = [
            'Transaction Type',
            'Beneficiary Code',
            'Beneficiary Account Number',
            'Instrument Amount',
            'Beneficiary Name',
            'Drawee Location',
            'Print Location',
            'Bene Address 1',
            'Bene Address 2',
            'Bene Address 3',
            'Bene Address 4',
            'Bene Address 5',
            'Instruction Reference Number',
            'Customer Reference Number',
            'Payment details 1',
            'Payment details 2',
            'Payment details 3',
            'Payment details 4',
            'Payment details 5',
            'Payment details 6',
            'Payment details 7',
            'Cheque Number',
            'Chq / Trn Date',
            'MICR Number',
            'IFC Code',
            'Bene Bank Name',
            'Bene Bank Branch Name',
            'Beneficiary email id'
        ]

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_style)
            worksheet.col(col).width = 5000  # Adjust default width

        # Write data
        row = 1
        for line in self.payment_line_ids:
            # Determine transaction type
            if line.bank_account_id and line.bank_account_id.bank_name and isinstance(line.bank_account_id.bank_name, str):
                transaction_type = 'I' if line.bank_account_id.bank_name.startswith('HDFC') else ('N' if line.amount < 200000 else 'R')
            else:
                transaction_type = 'N' if line.amount < 200000 else 'R'

            # Data mapping
            values = [
                transaction_type,
                'AGROTCX',
                line.account_no or '',
                line.amount,
                line.partner_id.name or '',
                '', '',  # Drawee Location, Print Location
                '', '', '', '', '',  # Bene Address 1-5
                line.instruction_reference or '',
                line.customer_reference or '',
                '', '', '', '', '', '', '',  # Payment details 1-7
                '',  # Cheque Number
                ',' + self.date.strftime('%d/%m/%Y'),  # Chq / Trn Date
                '',  # MICR Number
                line.ifsc_code or '',
                line.bank_name or '',
                '',  # Bene Bank Branch Name
                line.email or ''
            ]

            for col, value in enumerate(values):
                if col == 3:  # Instrument Amount
                    worksheet.write(row, col, value, amount_style)
                elif col == 22:  # Chq / Trn Date
                    worksheet.write(row, col, value, date_style)
                else:
                    worksheet.write(row, col, value, cell_style)

            row += 1

        # Save to buffer
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)

        filename = f"Payment_Sheet_{self.name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xls"

        # Create attachment
        attachment_vals = {
            'name': filename,
            'datas': base64.b64encode(output.read()),
            'res_model': 'payment.sheet',
            'res_id': self.id,
            'type': 'binary',
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
