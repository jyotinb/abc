from odoo import models, fields, api
from odoo.exceptions import ValidationError
import csv
import io
import base64
import json
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class DrkdsDashboardExport(models.Model):
    _name = 'drkds.dashboard.export'
    _description = 'Dashboard Data Export'

    name = fields.Char(string='Export Name')
    file_name = fields.Char(string='File Name')
    file_content = fields.Binary(string='File Content')
    export_format = fields.Selection([
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON')
    ], string='Export Format', required=True)

    def create_export(self, dashboard_data, export_format='csv'):
        """
        Create an export based on dashboard data
        """
        try:
            # Validate input
            if not dashboard_data:
                raise ValidationError("No data to export")

            # Prepare export file name
            file_name = f"dashboard_export_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"

            # Generate file content based on format
            export_methods = {
                'csv': self._export_to_csv,
                'xlsx': self._export_to_xlsx,
                'pdf': self._export_to_pdf,
                'json': self._export_to_json
            }

            export_method = export_methods.get(export_format)
            if not export_method:
                raise ValidationError(f"Unsupported export format: {export_format}")

            file_content = export_method(dashboard_data)

            # Create export record
            export = self.create({
                'name': f'Dashboard Export {fields.Datetime.now()}',
                'file_name': file_name,
                'file_content': base64.b64encode(file_content),
                'export_format': export_format
            })

            return export

        except Exception as e:
            raise ValidationError(f"Export creation failed: {str(e)}")

    def _export_to_csv(self, dashboard_data):
        """
        Export dashboard data to CSV
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers and data for metrics
        writer.writerow(['Metric', 'Value'])
        for metric_name, metric_value in dashboard_data.get('metrics', {}).items():
            writer.writerow([metric_name, str(metric_value)])

        return output.getvalue().encode('utf-8')

    def _export_to_xlsx(self, dashboard_data):
        """
        Export dashboard data to Excel
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Dashboard Data')
        
        # Write headers
        worksheet.write(0, 0, 'Metric')
        worksheet.write(0, 1, 'Value')
        
        # Write metrics
        for row, (metric_name, metric_value) in enumerate(dashboard_data.get('metrics', {}).items(), start=1):
            worksheet.write(row, 0, metric_name)
            worksheet.write(row, 1, str(metric_value))
        
        workbook.close()
        output.seek(0)
        return output.getvalue()

    def _export_to_pdf(self, dashboard_data):
        """
        Export dashboard data to PDF
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        
        # Prepare data for PDF table
        table_data = [['Metric', 'Value']]
        for metric_name, metric_value in dashboard_data.get('metrics', {}).items():
            table_data.append([metric_name, str(metric_value)])
        
        # Create table
        table = Table(table_data, colWidths=[3*inch, 3*inch])
        
        # Style table
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ])
        table.setStyle(style)
        
        # Build PDF
        doc.build([table])
        
        output.seek(0)
        return output.getvalue()

    def _export_to_json(self, dashboard_data):
        """
        Export dashboard data to JSON
        """
        return json.dumps(dashboard_data, indent=2).encode('utf-8')