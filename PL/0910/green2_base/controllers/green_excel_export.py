# green2_base/controllers/green_excel_export.py
from odoo import http
from odoo.http import request, content_disposition
import xlsxwriter
import io
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class GreenhouseExcelExport(http.Controller):
    
    @http.route('/greenhouse/export/excel/<int:project_id>', type='http', auth='user', methods=['GET'])
    def export_excel(self, project_id, **kwargs):
        """Export greenhouse project to professional Excel format"""
        try:
            project = request.env['green.master'].browse(project_id)
            if not project.exists():
                return request.not_found()
            
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            
            self._create_excel_report(workbook, project)
            
            workbook.close()
            output.seek(0)
            
            filename = f"Greenhouse_Report_{project.customer or 'Project'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filename = filename.replace(' ', '_').replace('/', '_')
            
            response = request.make_response(
                output.getvalue(),
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', content_disposition(filename))
                ]
            )
            output.close()
            return response
            
        except Exception as e:
            _logger.error(f"Error exporting Excel: {e}")
            return request.render('http_routing.http_error', {
                'status_code': 500,
                'status_message': 'Internal Server Error',
                'exception': str(e)
            })
    
    def _create_excel_report(self, workbook, project):
        """Create comprehensive Excel report with multiple worksheets"""
        
        styles = self._create_styles(workbook)
        
        self._create_summary_sheet(workbook, project, styles)
        self._create_structure_details_sheet(workbook, project, styles)
        self._create_component_management_sheet(workbook, project, styles)
        
        # Create module-specific sheets only if components exist
        if hasattr(project, 'asc_component_ids') and project.asc_component_ids:
            self._create_asc_components_sheet(workbook, project, styles)
        if project.frame_component_ids:
            self._create_frame_components_sheet(workbook, project, styles)
        if project.truss_component_ids:
            self._create_truss_components_sheet(workbook, project, styles)
        if hasattr(project, 'side_screen_component_ids') and project.side_screen_component_ids:
            self._create_side_screen_components_sheet(workbook, project, styles)
        if project.lower_component_ids:
            self._create_lower_components_sheet(workbook, project, styles)
        
        self._create_cost_analysis_sheet(workbook, project, styles)
        self._create_pipe_catalog_sheet(workbook, project, styles)
        
        # Allow extension by other modules
        self._create_additional_sheets(workbook, project, styles)
    
    def _create_additional_sheets(self, workbook, project, styles):
        """Hook for inherited modules to add sheets"""
        pass
    
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
            'subheader': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 11,
                'bold': True,
                'bg_color': '#ECF0F1',
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
            }),
            'total': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 11,
                'bold': True,
                'bg_color': '#E74C3C',
                'font_color': 'white',
                'border': 2,
                'align': 'right',
                'num_format': '#,##0.00'
            }),
        }
    
    # ... Continue with all sheet creation methods from original ...
    
    def _create_summary_sheet(self, workbook, project, styles):
        """Create project summary worksheet"""
        ws = workbook.add_worksheet('Project Summary')
        ws.set_column('A:A', 25)
        ws.set_column('B:B', 25)
        ws.set_column('C:C', 25)
        ws.set_column('D:D', 25)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 3, 'GREENHOUSE PROJECT SUMMARY', styles['title'])
        ws.set_row(row, 25)
        row += 2
        
        # Customer Information
        ws.merge_range(row, 0, row, 3, 'CUSTOMER INFORMATION', styles['header'])
        row += 1
        
        customer_data = [
            ('Customer Name:', project.customer or 'N/A'),
            ('Address:', project.address or 'N/A'),
            ('City:', project.city or 'N/A'),
            ('Mobile:', project.mobile or 'N/A'),
            ('Email:', project.email or 'N/A'),
            ('Reference:', project.reference or 'N/A'),
        ]
        
        for label, value in customer_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['data'])
            row += 1
        
        row += 1
        
        # Project Information
        ws.merge_range(row, 0, row, 3, 'PROJECT INFORMATION', styles['header'])
        row += 1
        
        project_data = [
            ('Structure Type:', project.structure_type),
            ('Plot Size:', project.plot_size or 'N/A'),
            ('Structure Size:', f"{round(project.structure_size, 2)} m²"),
            ('Number of Spans:', str(project.no_of_spans)),
            ('Number of Bays:', str(project.no_of_bays)),
            ('Total Span Length:', f"{project.total_span_length} m"),
            ('Total Bay Length:', f"{project.total_bay_length} m"),
            ('Top Ridge Height:', f"{project.top_ridge_height} m"),
            ('Column Height:', f"{project.column_height} m"),
            ('Gutter Type:', project.gutter_type.title()),
        ]
        
        for label, value in project_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['data'])
            row += 1
        
        row += 1
        
        # Cost Summary - Updated to include Side Screen
        ws.merge_range(row, 0, row, 3, 'COST SUMMARY', styles['header'])
        row += 1
        
        cost_data = []
        if project.total_asc_cost > 0:
            cost_data.append(('ASC Components:', project.total_asc_cost))
        cost_data.extend([
            ('Frame Components:', project.total_frame_cost),
            ('Truss Components:', project.total_truss_cost),
        ])
        
        # Calculate Side Screen cost separately if field exists
        if hasattr(project, 'total_side_screen_cost') and project.total_side_screen_cost > 0:
            cost_data.append(('Side Screen Components:', project.total_side_screen_cost))
        
        cost_data.append(('Lower Section:', project.total_lower_cost))
        
        for label, value in cost_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['currency'])
            row += 1
        
        # Grand Total
        ws.write(row, 0, 'GRAND TOTAL:', styles['subheader'])
        ws.write(row, 1, project.grand_total_cost, styles['total'])
        
        # Add generation info
        row += 3
        ws.write(row, 0, 'Report Generated:', styles['subheader'])
        ws.write(row, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), styles['data'])
    
    def _create_structure_details_sheet(self, workbook, project, styles):
        """Create structure details worksheet"""
        ws = workbook.add_worksheet('Structure Details')
        ws.set_column('A:A', 30)
        ws.set_column('B:B', 20)
        ws.set_column('C:C', 15)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 2, 'STRUCTURE DETAILS', styles['title'])
        row += 2
        
        # Dimensions
        ws.merge_range(row, 0, row, 2, 'DIMENSIONS', styles['header'])
        row += 1
        
        ws.write(row, 0, 'Parameter', styles['subheader'])
        ws.write(row, 1, 'Value', styles['subheader'])
        ws.write(row, 2, 'Unit', styles['subheader'])
        row += 1
        
        dimensions_data = [
            ('Total Span Length', project.total_span_length, 'm'),
            ('Total Bay Length', project.total_bay_length, 'm'),
            ('Calculated Span Length', project.span_length, 'm'),
            ('Calculated Bay Length', project.bay_length, 'm'),
            ('Span Width', project.span_width, 'm'),
            ('Bay Width', project.bay_width, 'm'),
            ('Structure Size', round(project.structure_size, 2), 'm²'),
            ('Top Ridge Height', project.top_ridge_height, 'm'),
            ('Column Height', project.column_height, 'm'),
            ('Bottom Height', project.bottom_height, 'm'),
            ('Arch Height', project.arch_height, 'm'),
            ('Big Arch Length', project.big_arch_length, 'm'),
            ('Small Arch Length', project.small_arch_length, 'm'),
            ('Gutter Length', project.gutter_length, 'm'),
            ('Foundation Length', project.foundation_length, 'm'),
        ]
        
        for param, value, unit in dimensions_data:
            ws.write(row, 0, param, styles['data'])
            ws.write(row, 1, value, styles['data_right'])
            ws.write(row, 2, unit, styles['data_center'])
            row += 1
        
        row += 2
        
        # Configuration
        ws.merge_range(row, 0, row, 2, 'CONFIGURATION', styles['header'])
        row += 1
        
        ws.write(row, 0, 'Parameter', styles['subheader'])
        ws.write(row, 1, 'Value', styles['subheader'])
        ws.write(row, 2, 'Notes', styles['subheader'])
        row += 1
        
        config_data = [
            ('Number of Spans', project.no_of_spans, 'Calculated'),
            ('Number of Bays', project.no_of_bays, 'Calculated'),
            ('Gutter Slope', project.gutter_slope, 'User Input'),
            ('Last Span Gutter', 'Yes' if project.last_span_gutter else 'No', 'User Input'),
            ('ASC Enabled', 'Yes' if project.is_side_coridoors else 'No', 'User Input'),
            ('Bottom Chord Required', 'Yes' if project.is_bottom_chord else 'No', 'User Input'),
            ('Side Screen Guard', 'Yes' if project.side_screen_guard else 'No', 'User Input'),
            ('Side Screen Guard Box', 'Yes' if project.side_screen_guard_box else 'No', 'User Input'),
            ('No of Curtains', project.no_of_curtains or 0, 'User Input'),
        ]
        
        for param, value, notes in config_data:
            ws.write(row, 0, param, styles['data'])
            ws.write(row, 1, value, styles['data_center'])
            ws.write(row, 2, notes, styles['data'])
            row += 1

    def _create_component_management_sheet(self, workbook, project, styles):
        """Create comprehensive Component Management worksheet"""
        ws = workbook.add_worksheet('Component Management')
        
        # Set column widths
        ws.set_column('A:A', 8)   # Section
        ws.set_column('B:B', 35)  # Component Name
        ws.set_column('C:C', 10)  # Nos
        ws.set_column('D:D', 12)  # Length
        ws.set_column('E:E', 15)  # Total Length
        ws.set_column('F:F', 20)  # Pipe Type
        ws.set_column('G:G', 12)  # Size
        ws.set_column('H:H', 10)  # WT
        ws.set_column('I:I', 12)  # Weight/Unit
        ws.set_column('J:J', 12)  # Rate/Kg
        ws.set_column('K:K', 15)  # Total Weight
        ws.set_column('L:L', 15)  # Total Cost
        ws.set_column('M:M', 10)  # Status
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 12, 'COMPLETE COMPONENT MANAGEMENT', styles['title'])
        row += 2
        
        # Headers
        headers = [
            'Section', 'Component Name', 'Nos', 'Length (m)', 'Total Length (m)', 
            'Pipe Type', 'Size (mm)', 'WT (mm)', 'Weight/Unit (kg/m)', 
            'Rate/Kg', 'Total Weight (kg)', 'Total Cost', 'Status'
        ]
        
        for col, header in enumerate(headers):
            ws.write(row, col, header, styles['header'])
        row += 1
        
        # Get Side Screen components separately
        side_screen_components = []
        other_lower_components = []
        
        for component in project.lower_component_ids:
            if component.name in ['Side Screen Roll Up Pipe', 'Side Screen Roll Up Pipe Joiner', 
                                 'Side Screen Guard', 'Side Screen Guard Box Pipe', 
                                 'Side Screen Guard Box H Pipe', 'Side Screen Guard Spacer', 
                                 'Side Screen Rollup Handles']:
                side_screen_components.append(component)
            else:
                other_lower_components.append(component)
        
        # Get side screen cost
        side_screen_cost = sum(comp.total_cost for comp in side_screen_components)
        
        # Get all components grouped by section - Updated with Side Screen
        sections = [
            ('ASC', project.asc_component_ids, project.total_asc_cost),
            ('FRAME', project.frame_component_ids, project.total_frame_cost),
            ('TRUSS', project.truss_component_ids, project.total_truss_cost),
            ('SIDE SCREEN', side_screen_components, side_screen_cost),
            ('LOWER', other_lower_components, project.total_lower_cost - side_screen_cost),
        ]
        
        grand_total_length = 0
        grand_total_weight = 0
        grand_total_cost = 0
        
        for section_name, components, section_cost in sections:
            if components:  # Only add section if it has components
                # Section header
                ws.merge_range(row, 0, row, 12, f'{section_name} COMPONENTS', styles['section_header'])
                row += 1
                
                section_total_length = 0
                section_total_weight = 0
                section_total_cost = 0
                
                for component in components:
                    # Determine pipe status
                    pipe_status = 'Selected' if component.pipe_id else 'Pending'
                    
                    ws.write(row, 0, section_name, styles['data_center'])
                    ws.write(row, 1, component.name, styles['data'])
                    ws.write(row, 2, component.nos, styles['data_center'])
                    ws.write(row, 3, round(component.length, 2), styles['data_right'])
                    ws.write(row, 4, round(component.total_length, 2), styles['data_right'])
                    ws.write(row, 5, component.pipe_type or 'Not Selected', styles['data'])
                    ws.write(row, 6, component.pipe_size or '-', styles['data_center'])
                    ws.write(row, 7, component.wall_thickness or '-', styles['data_center'])
                    ws.write(row, 8, round(component.weight_per_unit, 2) if component.weight_per_unit else 0, styles['data_right'])
                    ws.write(row, 9, round(component.rate_per_kg, 2) if component.rate_per_kg else 0, styles['data_right'])
                    ws.write(row, 10, round(component.total_weight, 2), styles['data_right'])
                    ws.write(row, 11, round(component.total_cost, 2), styles['currency'])
                    ws.write(row, 12, pipe_status, styles['data_center'])
                    
                    section_total_length += component.total_length
                    section_total_weight += component.total_weight
                    section_total_cost += component.total_cost
                    row += 1
                
                # Section total
                ws.write(row, 0, '', styles['section_total'])
                ws.write(row, 1, f'{section_name} SECTION TOTAL', styles['section_total'])
                ws.write(row, 2, '', styles['section_total'])
                ws.write(row, 3, '', styles['section_total'])
                ws.write(row, 4, round(section_total_length, 2), styles['section_total'])
                ws.write(row, 5, '', styles['section_total'])
                ws.write(row, 6, '', styles['section_total'])
                ws.write(row, 7, '', styles['section_total'])
                ws.write(row, 8, '', styles['section_total'])
                ws.write(row, 9, '', styles['section_total'])
                ws.write(row, 10, round(section_total_weight, 2), styles['section_total'])
                ws.write(row, 11, round(section_total_cost, 2), styles['section_total'])
                ws.write(row, 12, '', styles['section_total'])
                row += 2
                
                grand_total_length += section_total_length
                grand_total_weight += section_total_weight
                grand_total_cost += section_total_cost
        
        # Grand Total
        ws.write(row, 0, '', styles['total'])
        ws.write(row, 1, 'PROJECT GRAND TOTAL', styles['total'])
        ws.write(row, 2, '', styles['total'])
        ws.write(row, 3, '', styles['total'])
        ws.write(row, 4, round(grand_total_length, 2), styles['total'])
        ws.write(row, 5, '', styles['total'])
        ws.write(row, 6, '', styles['total'])
        ws.write(row, 7, '', styles['total'])
        ws.write(row, 8, '', styles['total'])
        ws.write(row, 9, '', styles['total'])
        ws.write(row, 10, round(grand_total_weight, 2), styles['total'])
        ws.write(row, 11, round(grand_total_cost, 2), styles['total'])
        ws.write(row, 12, '', styles['total'])
        
        # Add summary statistics
        row += 3
        ws.write(row, 0, 'SUMMARY STATISTICS:', styles['subheader'])
        row += 1
        
        # Get all components for statistics
        all_components = (project.asc_component_ids + project.frame_component_ids + 
                         project.truss_component_ids + project.lower_component_ids)
        
        total_components = len(all_components)
        components_with_pipes = sum(1 for component in all_components if component.pipe_id)
        components_without_pipes = total_components - components_with_pipes
        
        summary_data = [
            ('Total Components:', total_components),
            ('Components with Pipes:', components_with_pipes),
            ('Components without Pipes:', components_without_pipes),
            ('Structure Size (m²):', round(project.structure_size, 2)),
            ('Cost per m²:', round(grand_total_cost / project.structure_size, 2) if project.structure_size > 0 else 0),
        ]
        
        for label, value in summary_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['data_right'])
            row += 1
    
    def _create_component_sheet(self, workbook, project, styles, components, sheet_name, section_total):
        """Generic method to create component sheets"""
        if not components:
            return
            
        ws = workbook.add_worksheet(sheet_name)
        
        # Set column widths
        ws.set_column('A:A', 35)  # Component Name
        ws.set_column('B:B', 10)  # Nos
        ws.set_column('C:C', 12)  # Length
        ws.set_column('D:D', 15)  # Total Length
        ws.set_column('E:E', 20)  # Pipe Type
        ws.set_column('F:F', 12)  # Size
        ws.set_column('G:G', 10)  # WT
        ws.set_column('H:H', 12)  # Weight/Unit
        ws.set_column('I:I', 12)  # Rate/Kg
        ws.set_column('J:J', 15)  # Total Weight
        ws.set_column('K:K', 15)  # Total Cost
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 10, f'{sheet_name.upper()}', styles['title'])
        row += 2
        
        # Headers
        headers = [
            'Component Name', 'Nos', 'Length (m)', 'Total Length (m)', 
            'Pipe Type', 'Size (mm)', 'WT (mm)', 'Weight/Unit (kg/m)', 
            'Rate/Kg', 'Total Weight (kg)', 'Total Cost'
        ]
        
        for col, header in enumerate(headers):
            ws.write(row, col, header, styles['header'])
        row += 1
        
        # Component data
        total_length = 0
        total_weight = 0
        total_cost = 0
        
        for component in components:
            ws.write(row, 0, component.name, styles['data'])
            ws.write(row, 1, component.nos, styles['data_center'])
            ws.write(row, 2, round(component.length, 2), styles['data_right'])
            ws.write(row, 3, round(component.total_length, 2), styles['data_right'])
            ws.write(row, 4, component.pipe_type or 'Not Selected', styles['data'])
            ws.write(row, 5, component.pipe_size or '-', styles['data_center'])
            ws.write(row, 6, component.wall_thickness or '-', styles['data_center'])
            ws.write(row, 7, round(component.weight_per_unit, 2) if component.weight_per_unit else 0, styles['data_right'])
            ws.write(row, 8, round(component.rate_per_kg, 2) if component.rate_per_kg else 0, styles['data_right'])
            ws.write(row, 9, round(component.total_weight, 2), styles['data_right'])
            ws.write(row, 10, round(component.total_cost, 2), styles['currency'])
            
            total_length += component.total_length
            total_weight += component.total_weight
            total_cost += component.total_cost
            row += 1
        
        # Totals row
        ws.write(row, 0, 'SECTION TOTAL', styles['section_total'])
        ws.write(row, 1, '', styles['section_total'])
        ws.write(row, 2, '', styles['section_total'])
        ws.write(row, 3, round(total_length, 2), styles['section_total'])
        ws.write(row, 4, '', styles['section_total'])
        ws.write(row, 5, '', styles['section_total'])
        ws.write(row, 6, '', styles['section_total'])
        ws.write(row, 7, '', styles['section_total'])
        ws.write(row, 8, '', styles['section_total'])
        ws.write(row, 9, round(total_weight, 2), styles['section_total'])
        ws.write(row, 10, round(section_total, 2), styles['section_total'])
    
    def _create_asc_components_sheet(self, workbook, project, styles):
        """Create ASC components sheet"""
        if project.asc_component_ids:
            self._create_component_sheet(
                workbook, project, styles, 
                project.asc_component_ids, 
                'ASC Components', 
                project.total_asc_cost
            )
    
    def _create_frame_components_sheet(self, workbook, project, styles):
        """Create Frame components sheet"""
        self._create_component_sheet(
            workbook, project, styles, 
            project.frame_component_ids, 
            'Frame Components', 
            project.total_frame_cost
        )
    
    def _create_truss_components_sheet(self, workbook, project, styles):
        """Create Truss components sheet"""
        self._create_component_sheet(
            workbook, project, styles, 
            project.truss_component_ids, 
            'Truss Components', 
            project.total_truss_cost
        )
    
    def _create_side_screen_components_sheet(self, workbook, project, styles):
        """Create Side Screen components sheet"""
        # Filter Side Screen components from lower_component_ids
        side_screen_components = []
        for component in project.lower_component_ids:
            if component.name in ['Side Screen Roll Up Pipe', 'Side Screen Roll Up Pipe Joiner', 
                                 'Side Screen Guard', 'Side Screen Guard Box Pipe', 
                                 'Side Screen Guard Box H Pipe', 'Side Screen Guard Spacer', 
                                 'Side Screen Rollup Handles']:
                side_screen_components.append(component)
        
        if side_screen_components:
            side_screen_cost = sum(comp.total_cost for comp in side_screen_components)
            self._create_component_sheet(
                workbook, project, styles, 
                side_screen_components, 
                'Side Screen Components', 
                side_screen_cost
            )
    
    def _create_lower_components_sheet(self, workbook, project, styles):
        """Create Lower Section components sheet (excluding Side Screen)"""
        # Filter out Side Screen components
        lower_components = []
        for component in project.lower_component_ids:
            if component.name not in ['Side Screen Roll Up Pipe', 'Side Screen Roll Up Pipe Joiner', 
                                     'Side Screen Guard', 'Side Screen Guard Box Pipe', 
                                     'Side Screen Guard Box H Pipe', 'Side Screen Guard Spacer', 
                                     'Side Screen Rollup Handles']:
                lower_components.append(component)
        
        if lower_components:
            lower_cost = sum(comp.total_cost for comp in lower_components)
            self._create_component_sheet(
                workbook, project, styles, 
                lower_components, 
                'Lower Section Components', 
                lower_cost
            )
    
    def _create_cost_analysis_sheet(self, workbook, project, styles):
        """Create cost analysis worksheet"""
        ws = workbook.add_worksheet('Cost Analysis')
        ws.set_column('A:A', 30)
        ws.set_column('B:B', 20)
        ws.set_column('C:C', 15)
        ws.set_column('D:D', 15)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 3, 'COST ANALYSIS', styles['title'])
        row += 2
        
        # Section breakdown
        ws.write(row, 0, 'Section', styles['header'])
        ws.write(row, 1, 'Total Cost', styles['header'])
        ws.write(row, 2, 'Percentage', styles['header'])
        ws.write(row, 3, 'Components Count', styles['header'])
        row += 1
        
        # Separate Side Screen components
        side_screen_components = []
        other_lower_components = []
        
        for component in project.lower_component_ids:
            if component.name in ['Side Screen Roll Up Pipe', 'Side Screen Roll Up Pipe Joiner', 
                                 'Side Screen Guard', 'Side Screen Guard Box Pipe', 
                                 'Side Screen Guard Box H Pipe', 'Side Screen Guard Spacer', 
                                 'Side Screen Rollup Handles']:
                side_screen_components.append(component)
            else:
                other_lower_components.append(component)
        
        side_screen_cost = sum(comp.total_cost for comp in side_screen_components)
        lower_cost = sum(comp.total_cost for comp in other_lower_components)
        
        sections_data = []
        if project.total_asc_cost > 0:
            sections_data.append(('ASC Components', project.total_asc_cost, len(project.asc_component_ids)))
        sections_data.extend([
            ('Frame Components', project.total_frame_cost, len(project.frame_component_ids)),
            ('Truss Components', project.total_truss_cost, len(project.truss_component_ids)),
        ])
        if side_screen_components:
            sections_data.append(('Side Screen Components', side_screen_cost, len(side_screen_components)))
        if other_lower_components:
            sections_data.append(('Lower Section', lower_cost, len(other_lower_components)))
        
        for section_name, cost, count in sections_data:
            percentage = (cost / project.grand_total_cost * 100) if project.grand_total_cost > 0 else 0
            ws.write(row, 0, section_name, styles['data'])
            ws.write(row, 1, cost, styles['currency'])
            ws.write(row, 2, f"{round(percentage, 1)}%", styles['data_center'])
            ws.write(row, 3, count, styles['data_center'])
            row += 1
        
        # Grand total
        ws.write(row, 0, 'GRAND TOTAL', styles['total'])
        ws.write(row, 1, project.grand_total_cost, styles['total'])
        ws.write(row, 2, '100.0%', styles['total'])
        total_components = len(project.asc_component_ids + project.frame_component_ids + 
                              project.truss_component_ids + project.lower_component_ids)
        ws.write(row, 3, total_components, styles['total'])
        
        row += 3
        
        # Cost per square meter
        if project.structure_size > 0:
            cost_per_sqm = project.grand_total_cost / project.structure_size
            ws.write(row, 0, 'Cost per m²:', styles['subheader'])
            ws.write(row, 1, cost_per_sqm, styles['currency'])
            row += 1
        
        # Components without pipes
        all_components = (project.asc_component_ids + project.frame_component_ids + 
                         project.truss_component_ids + project.lower_component_ids)
        components_without_pipes = len([c for c in all_components if not c.pipe_id])
        
        if components_without_pipes > 0:
            row += 1
            ws.write(row, 0, 'Components without pipes:', styles['subheader'])
            ws.write(row, 1, components_without_pipes, styles['data_center'])
            ws.write(row, 2, '⚠️ Attention needed', styles['data'])
    
    def _create_pipe_catalog_sheet(self, workbook, project, styles):
        """Create pipe catalog worksheet showing all used pipes"""
        ws = workbook.add_worksheet('Pipe Catalog')
        ws.set_column('A:A', 25)  # Pipe Type
        ws.set_column('B:B', 15)  # Size
        ws.set_column('C:C', 15)  # Wall Thickness
        ws.set_column('D:D', 15)  # Weight/Unit
        ws.set_column('E:E', 15)  # Rate/Kg
        ws.set_column('F:F', 20)  # Used in Components
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 5, 'PIPE CATALOG', styles['title'])
        row += 2
        
        # Headers
        headers = ['Pipe Type', 'Size (mm)', 'Wall Thickness (mm)', 'Weight/Unit (kg/m)', 'Rate/Kg', 'Used in Components']
        for col, header in enumerate(headers):
            ws.write(row, col, header, styles['header'])
        row += 1
        
        # Get unique pipes used in project
        all_components = (project.asc_component_ids + project.frame_component_ids + 
                         project.truss_component_ids + project.lower_component_ids)
        
        pipes_used = {}
        for component in all_components:
            if component.pipe_id:
                pipe_key = (component.pipe_id.id, component.pipe_type, 
                           component.pipe_size, component.wall_thickness)
                if pipe_key not in pipes_used:
                    pipes_used[pipe_key] = {
                        'pipe': component.pipe_id,
                        'components': []
                    }
                pipes_used[pipe_key]['components'].append(component.name)
        
        # Write pipe data
        for pipe_info in pipes_used.values():
            pipe = pipe_info['pipe']
            components_list = ', '.join(pipe_info['components'][:3])  # Show first 3 components
            if len(pipe_info['components']) > 3:
                components_list += f' (+{len(pipe_info["components"]) - 3} more)'
            
            ws.write(row, 0, pipe.name.name if pipe.name else 'N/A', styles['data'])
            ws.write(row, 1, pipe.pipe_size.size_in_mm if pipe.pipe_size else 'N/A', styles['data_center'])
            ws.write(row, 2, pipe.wall_thickness.thickness_in_mm if pipe.wall_thickness else 'N/A', styles['data_center'])
            ws.write(row, 3, round(pipe.weight, 2) if pipe.weight else 0, styles['data_right'])
            ws.write(row, 4, round(pipe.rate, 2) if pipe.rate else 0, styles['data_right'])
            ws.write(row, 5, components_list, styles['data'])
            row += 1