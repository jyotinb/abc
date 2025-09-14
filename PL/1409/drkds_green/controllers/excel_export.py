import io
import xlsxwriter
from odoo import http
from odoo.http import request, Response
import logging

_logger = logging.getLogger(__name__)


class GreenhouseExcelExport(http.Controller):
    
    @http.route('/greenhouse/export_excel/<int:project_id>', type='http', auth='user')
    def export_excel(self, project_id, **kwargs):
        """Export greenhouse project to Excel"""
        try:
            project = request.env['green.master'].browse(project_id)
            if not project.exists():
                return Response("Project not found", status=404)
            
            # Create Excel file in memory
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            
            # Create Excel report
            self._create_excel_report(workbook, project)
            
            workbook.close()
            output.seek(0)
            
            # Prepare response
            filename = f"greenhouse_project_{project.name}_{project.customer}.xlsx".replace(' ', '_')
            
            return Response(
                output.read(),
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', f'attachment; filename="{filename}"'),
                    ('Content-Length', len(output.getvalue()))
                ]
            )
            
        except Exception as e:
            _logger.error(f"Error exporting Excel: {e}")
            return Response(f"Error exporting Excel: {str(e)}", status=500)
    
    def _create_excel_report(self, workbook, project):
        """Create comprehensive Excel report"""
        styles = self._create_styles(workbook)
        
        # Create worksheets
        self._create_summary_sheet(workbook, project, styles)
        self._create_component_management_sheet(workbook, project, styles)
    
    def _create_styles(self, workbook):
        """Create formatting styles"""
        return {
            'title': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 18,
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#2C3E50',
                'font_color': 'white',
                'border': 2
            }),
            'header': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 12,
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#34495E',
                'font_color': 'white',
                'border': 1
            }),
            'data': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 10,
                'border': 1,
                'valign': 'vcenter'
            }),
            'currency': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 10,
                'border': 1,
                'align': 'right',
                'valign': 'vcenter',
                'num_format': '#,##0.00'
            })
        }
    
    def _create_summary_sheet(self, workbook, project, styles):
        """Create project summary sheet"""
        ws = workbook.add_worksheet('Project Summary')
        
        # Set column widths
        ws.set_column('A:D', 25)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 3, 'GREENHOUSE PROJECT SUMMARY', styles['title'])
        row += 2
        
        # Project data
        project_data = [
            ('Project Name:', project.name or ''),
            ('Customer:', project.customer or ''),
            ('Structure Size (m²):', round(project.structure_size, 2)),
            ('Grand Total Cost:', project.grand_total_cost),
        ]
        
        for label, value in project_data:
            ws.write(row, 0, label, styles['header'])
            style = styles['currency'] if 'Cost' in label else styles['data']
            ws.write(row, 1, value, style)
            row += 1
    
    def _create_component_management_sheet(self, workbook, project, styles):
        """Create component management sheet"""
        ws = workbook.add_worksheet('Components')
        
        # Set column widths
        ws.set_column('A:A', 8)
        ws.set_column('B:B', 35)
        ws.set_column('C:C', 10)
        ws.set_column('D:D', 15)
        ws.set_column('E:E', 15)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 4, 'COMPONENT MANAGEMENT', styles['title'])
        row += 2
        
        # Headers
        headers = ['Section', 'Component Name', 'Qty', 'Length', 'Total Cost']
        
        for col, header in enumerate(headers):
            ws.write(row, col, header, styles['header'])
        row += 1
        
        # Component data
        all_components = (project.frame_component_ids + project.truss_component_ids + 
                         project.asc_component_ids + project.side_screen_component_ids + 
                         project.lower_component_ids)
        
        for component in all_components:
            ws.write(row, 0, component.section.upper(), styles['data'])
            ws.write(row, 1, component.name, styles['data'])
            ws.write(row, 2, component.nos, styles['data'])
            ws.write(row, 3, round(component.length, 2), styles['data'])
            ws.write(row, 4, round(component.total_cost, 2), styles['currency'])
            row += 1