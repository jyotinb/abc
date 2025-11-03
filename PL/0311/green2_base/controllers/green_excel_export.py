# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, content_disposition
import xlsxwriter
import io
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class GreenhouseExcelExport(http.Controller):
    
    # ═══════════════════════════════════════════════════════════════
    # COMPONENT REGISTRY - Modules auto-register here
    # ═══════════════════════════════════════════════════════════════
    _component_registry = {}
    
    @classmethod
    def register_component_section(cls, field_name, config):
        """
        Allow modules to register their component sections dynamically.
        
        Usage in any module:
            GreenhouseExcelExport.register_component_section('your_component_ids', {
                'sheet_name': 'Your Components',
                'section_name': 'YOUR_SECTION',
                'cost_field': 'total_your_cost',
                'priority': 50,
                'is_accessory': False
            })
        """
        cls._component_registry[field_name] = config
        _logger.info(f"Registered component section: {field_name} -> {config['sheet_name']}")
    
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
            _logger.error(f"Error exporting Excel for project {project_id}: {str(e)}", exc_info=True)
            return request.render('http_routing.http_error', {
                'status_code': 500,
                'status_message': 'Internal Server Error',
                'exception': str(e)
            })
    
    def _create_excel_report(self, workbook, project):
        """Create comprehensive Excel report with multiple worksheets"""
        try:
            styles = self._create_styles(workbook)
            
            # Always create these base sheets
            self._create_summary_sheet(workbook, project, styles)
            self._create_structure_details_sheet(workbook, project, styles)
            self._create_component_management_sheet(workbook, project, styles)
            
            # DYNAMIC: Get all registered component sections
            component_sections = self._get_all_component_sections(project)
            
            for section_info in component_sections:
                if section_info['components']:
                    self._create_component_sheet(
                        workbook, project, styles,
                        section_info['components'],
                        section_info['sheet_name'],
                        section_info['total_cost'],
                        section_info.get('is_accessory', False)
                    )
            
            # Always create these analysis sheets
            self._create_cost_analysis_sheet(workbook, project, styles)
            self._create_pipe_catalog_sheet(workbook, project, styles)
            
            # Allow extension by other modules
            self._create_additional_sheets(workbook, project, styles)
            
        except Exception as e:
            _logger.error(f"Error creating Excel report: {str(e)}", exc_info=True)
            raise
    
    def _get_all_component_sections(self, project):
        """
        Get all registered component sections from registry.
        Modules register themselves using register_component_section().
        """
        sections = []
        
        # Iterate through all registered component fields
        for field_name, config in self._component_registry.items():
            if hasattr(project, field_name):
                components = getattr(project, field_name, None)
                
                if components:  # If field exists and has records
                    # Get cost field
                    total_cost = 0
                    cost_field = config.get('cost_field')
                    if cost_field and hasattr(project, cost_field):
                        total_cost = getattr(project, cost_field, 0)
                    
                    sections.append({
                        'field_name': field_name,
                        'sheet_name': config['sheet_name'],
                        'section_name': config['section_name'],
                        'components': components,
                        'total_cost': total_cost,
                        'priority': config.get('priority', 999),
                        'is_accessory': config.get('is_accessory', False)
                    })
        
        # Sort by priority
        sections.sort(key=lambda x: x['priority'])
        
        _logger.info(f"Excel Export: Found {len(sections)} component sections from registry")
        return sections
    
    def _create_additional_sheets(self, workbook, project, styles):
        """Hook for inherited modules to add custom sheets"""
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
            'section_header': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 11,
                'bold': True,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#5DADE2',
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
            'data_center': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 10,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            }),
            'data_right': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 10,
                'border': 1,
                'align': 'right',
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
            'section_total': workbook.add_format({
                'font_name': 'Arial',
                'font_size': 10,
                'bold': True,
                'bg_color': '#D5DBDB',
                'border': 1,
                'align': 'right',
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
    
    def _create_summary_sheet(self, workbook, project, styles):
        """Create project summary worksheet"""
        ws = workbook.add_worksheet('Project Summary')
        ws.set_column('A:A', 25)
        ws.set_column('B:B', 25)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 1, 'GREENHOUSE PROJECT SUMMARY', styles['title'])
        ws.set_row(row, 25)
        row += 2
        
        # Customer Information
        ws.merge_range(row, 0, row, 1, 'CUSTOMER INFORMATION', styles['header'])
        row += 1
        
        customer_data = [
            ('Customer Name:', getattr(project, 'customer', 'N/A') or 'N/A'),
            ('Address:', getattr(project, 'address', 'N/A') or 'N/A'),
            ('City:', getattr(project, 'city', 'N/A') or 'N/A'),
            ('Mobile:', getattr(project, 'mobile', 'N/A') or 'N/A'),
            ('Email:', getattr(project, 'email', 'N/A') or 'N/A'),
        ]
        
        for label, value in customer_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['data'])
            row += 1
        
        row += 1
        
        # Project Information
        ws.merge_range(row, 0, row, 1, 'PROJECT INFORMATION', styles['header'])
        row += 1
        
        project_data = [
            ('Structure Size:', f"{round(project.structure_size, 2)} m²"),
            ('Number of Spans:', str(project.no_of_spans)),
            ('Number of Bays:', str(project.no_of_bays)),
        ]
        
        for label, value in project_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['data'])
            row += 1
        
        row += 1
        
        # DYNAMIC Cost Summary
        ws.merge_range(row, 0, row, 1, 'COST SUMMARY', styles['header'])
        row += 1
        
        # Get all sections dynamically from registry
        all_sections = self._get_all_component_sections(project)
        
        for section_info in all_sections:
            label = f"{section_info['sheet_name']}:"
            value = section_info['total_cost']
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['currency'])
            row += 1
        
        # Grand Total
        grand_total = sum(section['total_cost'] for section in all_sections)
        ws.write(row, 0, 'GRAND TOTAL:', styles['subheader'])
        ws.write(row, 1, grand_total, styles['total'])
        
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
        ws.merge_range(row, 0, row, 2, 'STRUCTURE DETAILS', styles['title'])
        row += 2
        
        ws.merge_range(row, 0, row, 2, 'DIMENSIONS', styles['header'])
        row += 1
        
        ws.write(row, 0, 'Parameter', styles['subheader'])
        ws.write(row, 1, 'Value', styles['subheader'])
        ws.write(row, 2, 'Unit', styles['subheader'])
        row += 1
        
        dimensions_data = [
            ('Structure Size', round(project.structure_size, 2), 'm²'),
            ('Number of Spans', project.no_of_spans, 'nos'),
            ('Number of Bays', project.no_of_bays, 'nos'),
        ]
        
        for param, value, unit in dimensions_data:
            ws.write(row, 0, param, styles['data'])
            ws.write(row, 1, value, styles['data_right'])
            ws.write(row, 2, unit, styles['data_center'])
            row += 1

    def _create_component_management_sheet(self, workbook, project, styles):
        """Create comprehensive Component Management worksheet"""
        ws = workbook.add_worksheet('Component Management')
        
        # Set column widths
        ws.set_column('A:A', 15)
        ws.set_column('B:B', 35)
        ws.set_column('C:C', 10)
        ws.set_column('D:D', 12)
        ws.set_column('E:E', 15)
        ws.set_column('F:F', 20)
        ws.set_column('G:G', 12)
        ws.set_column('H:H', 10)
        ws.set_column('I:I', 12)
        ws.set_column('J:J', 12)
        ws.set_column('K:K', 15)
        ws.set_column('L:L', 15)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 11, 'COMPLETE COMPONENT MANAGEMENT', styles['title'])
        row += 2
        
        # Headers
        headers = [
            'Section', 'Component Name', 'Nos', 'Length (m)', 'Total Length (m)', 
            'Pipe Type / Size', 'Size (mm)', 'WT (mm)', 'Weight/Unit (kg/m)', 
            'Rate/Kg', 'Total Weight (kg)', 'Total Cost'
        ]
        
        for col, header in enumerate(headers):
            ws.write(row, col, header, styles['header'])
        row += 1
        
        # Get all registered sections
        all_sections = self._get_all_component_sections(project)
        
        grand_total_length = 0
        grand_total_weight = 0
        grand_total_cost = 0
        
        for section_info in all_sections:
            components = section_info['components']
            section_name = section_info['section_name']
            is_accessory = section_info.get('is_accessory', False)
            
            if components:
                # Section header
                ws.merge_range(row, 0, row, 11, f'{section_name} COMPONENTS', styles['section_header'])
                row += 1
                
                section_total_length = 0
                section_total_weight = 0
                section_total_cost = 0
                
                for component in components:
                    is_pipe_component = hasattr(component, 'pipe_type')
                    
                    ws.write(row, 0, section_name, styles['data_center'])
                    ws.write(row, 1, component.name, styles['data'])
                    ws.write(row, 2, component.nos, styles['data_center'])
                    
                    if is_pipe_component and not is_accessory:
                        ws.write(row, 3, round(component.length, 2), styles['data_right'])
                        ws.write(row, 4, round(component.total_length, 2), styles['data_right'])
                        ws.write(row, 5, component.pipe_type or 'Not Selected', styles['data'])
                        ws.write(row, 6, component.pipe_size or '-', styles['data_center'])
                        ws.write(row, 7, component.wall_thickness or '-', styles['data_center'])
                        ws.write(row, 8, round(component.weight_per_unit, 2) if component.weight_per_unit else 0, styles['data_right'])
                        ws.write(row, 9, round(component.rate_per_kg, 2) if component.rate_per_kg else 0, styles['data_right'])
                        ws.write(row, 10, round(component.total_weight, 2), styles['data_right'])
                        
                        section_total_length += component.total_length
                        section_total_weight += component.total_weight
                    else:
                        ws.write(row, 3, '-', styles['data_center'])
                        ws.write(row, 4, '-', styles['data_center'])
                        ws.write(row, 5, getattr(component, 'size_specification', '-') or '-', styles['data'])
                        ws.write(row, 6, '-', styles['data_center'])
                        ws.write(row, 7, '-', styles['data_center'])
                        ws.write(row, 8, '-', styles['data_center'])
                        ws.write(row, 9, round(getattr(component, 'unit_price', 0), 2), styles['data_right'])
                        ws.write(row, 10, '-', styles['data_center'])
                    
                    ws.write(row, 11, round(component.total_cost, 2), styles['currency'])
                    section_total_cost += component.total_cost
                    row += 1
                
                # Section Total
                ws.write(row, 0, '', styles['section_total'])
                ws.write(row, 1, f'{section_name} TOTAL', styles['section_total'])
                ws.write(row, 2, '', styles['section_total'])
                ws.write(row, 3, '', styles['section_total'])
                ws.write(row, 4, round(section_total_length, 2) if section_total_length > 0 else '-', styles['section_total'])
                ws.write(row, 5, '', styles['section_total'])
                ws.write(row, 6, '', styles['section_total'])
                ws.write(row, 7, '', styles['section_total'])
                ws.write(row, 8, '', styles['section_total'])
                ws.write(row, 9, '', styles['section_total'])
                ws.write(row, 10, round(section_total_weight, 2) if section_total_weight > 0 else '-', styles['section_total'])
                ws.write(row, 11, round(section_total_cost, 2), styles['section_total'])
                row += 2
                
                grand_total_length += section_total_length
                grand_total_weight += section_total_weight
                grand_total_cost += section_total_cost
        
        # Grand Total
        ws.write(row, 0, '', styles['total'])
        ws.write(row, 1, 'PROJECT GRAND TOTAL', styles['total'])
        for col in range(2, 11):
            ws.write(row, col, '', styles['total'])
        ws.write(row, 4, round(grand_total_length, 2) if grand_total_length > 0 else '-', styles['total'])
        ws.write(row, 10, round(grand_total_weight, 2) if grand_total_weight > 0 else '-', styles['total'])
        ws.write(row, 11, round(grand_total_cost, 2), styles['total'])
    
    def _create_component_sheet(self, workbook, project, styles, components, sheet_name, section_total, is_accessory=False):
        """Generic method to create component sheets"""
        if not components:
            return
            
        ws = workbook.add_worksheet(sheet_name)
        
        if is_accessory:
            # Accessory format
            ws.set_column('A:A', 35)
            ws.set_column('B:B', 10)
            ws.set_column('C:C', 20)
            ws.set_column('D:D', 15)
            ws.set_column('E:E', 15)
            
            row = 0
            ws.merge_range(row, 0, row, 4, f'{sheet_name.upper()}', styles['title'])
            row += 2
            
            headers = ['Component Name', 'Quantity', 'Size/Type', 'Unit Price', 'Total Cost']
            for col, header in enumerate(headers):
                ws.write(row, col, header, styles['header'])
            row += 1
            
            total_cost = 0
            for component in components:
                ws.write(row, 0, component.name, styles['data'])
                ws.write(row, 1, component.nos, styles['data_center'])
                ws.write(row, 2, getattr(component, 'size_specification', 'N/A') or 'N/A', styles['data_center'])
                ws.write(row, 3, round(getattr(component, 'unit_price', 0), 2), styles['data_right'])
                ws.write(row, 4, round(component.total_cost, 2), styles['currency'])
                total_cost += component.total_cost
                row += 1
            
            ws.write(row, 0, 'SECTION TOTAL', styles['section_total'])
            for col in range(1, 4):
                ws.write(row, col, '', styles['section_total'])
            ws.write(row, 4, round(total_cost, 2), styles['section_total'])
        else:
            # Pipe format
            ws.set_column('A:A', 35)
            ws.set_column('B:B', 10)
            ws.set_column('C:C', 12)
            ws.set_column('D:D', 15)
            ws.set_column('E:E', 20)
            ws.set_column('F:F', 12)
            ws.set_column('G:G', 10)
            ws.set_column('H:H', 12)
            ws.set_column('I:I', 12)
            ws.set_column('J:J', 15)
            ws.set_column('K:K', 15)
            
            row = 0
            ws.merge_range(row, 0, row, 10, f'{sheet_name.upper()}', styles['title'])
            row += 2
            
            headers = [
                'Component Name', 'Nos', 'Length (m)', 'Total Length (m)', 
                'Pipe Type', 'Size (mm)', 'WT (mm)', 'Weight/Unit (kg/m)', 
                'Rate/Kg', 'Total Weight (kg)', 'Total Cost'
            ]
            
            for col, header in enumerate(headers):
                ws.write(row, col, header, styles['header'])
            row += 1
            
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
            
            ws.write(row, 0, 'SECTION TOTAL', styles['section_total'])
            for col in range(1, 3):
                ws.write(row, col, '', styles['section_total'])
            ws.write(row, 3, round(total_length, 2), styles['section_total'])
            for col in range(4, 9):
                ws.write(row, col, '', styles['section_total'])
            ws.write(row, 9, round(total_weight, 2), styles['section_total'])
            ws.write(row, 10, round(section_total, 2), styles['section_total'])
    
    def _create_cost_analysis_sheet(self, workbook, project, styles):
        """Create cost analysis worksheet"""
        ws = workbook.add_worksheet('Cost Analysis')
        ws.set_column('A:A', 30)
        ws.set_column('B:B', 20)
        ws.set_column('C:C', 15)
        ws.set_column('D:D', 15)
        
        row = 0
        ws.merge_range(row, 0, row, 3, 'COST ANALYSIS', styles['title'])
        row += 2
        
        ws.write(row, 0, 'Section', styles['header'])
        ws.write(row, 1, 'Total Cost', styles['header'])
        ws.write(row, 2, 'Percentage', styles['header'])
        ws.write(row, 3, 'Components Count', styles['header'])
        row += 1
        
        all_sections = self._get_all_component_sections(project)
        grand_total = sum(section['total_cost'] for section in all_sections)
        
        for section_info in all_sections:
            section_name = section_info['sheet_name']
            total_cost = section_info['total_cost']
            component_count = len(section_info['components'])
            percentage = (total_cost / grand_total * 100) if grand_total > 0 else 0
            
            ws.write(row, 0, section_name, styles['data'])
            ws.write(row, 1, round(total_cost, 2), styles['currency'])
            ws.write(row, 2, f"{round(percentage, 1)}%", styles['data_center'])
            ws.write(row, 3, component_count, styles['data_center'])
            row += 1
        
        total_components = sum(len(section['components']) for section in all_sections)
        ws.write(row, 0, 'GRAND TOTAL', styles['total'])
        ws.write(row, 1, round(grand_total, 2), styles['total'])
        ws.write(row, 2, '100.0%', styles['total'])
        ws.write(row, 3, total_components, styles['total'])
    
    def _create_pipe_catalog_sheet(self, workbook, project, styles):
        """Create detailed pipe catalog worksheet with length-wise quantities"""
        ws = workbook.add_worksheet('Pipe Catalog')
        
        row = 0
        ws.merge_range(row, 0, row, 10, 'PIPE CATALOG - DETAILED', styles['title'])
        row += 2
        
        # Get all pipe components from all sections
        all_sections = self._get_all_component_sections(project)
        
        # Collect pipe data with length breakdown
        pipes_data = {}
        
        for section_info in all_sections:
            if not section_info.get('is_accessory', False):  # Only pipe components
                for component in section_info['components']:
                    if hasattr(component, 'pipe_id') and component.pipe_id:
                        pipe_key = f"{component.pipe_type}_{component.pipe_size}_{component.wall_thickness}"
                        
                        if pipe_key not in pipes_data:
                            pipes_data[pipe_key] = {
                                'type': component.pipe_type,
                                'size': component.pipe_size,
                                'wt': component.wall_thickness,
                                'rate': component.rate_per_kg,
                                'sections': set(),
                                'lengths': {},  # Length -> quantity mapping
                                'total_meters': 0,
                                'total_nos': 0
                            }
                        
                        pipes_data[pipe_key]['sections'].add(section_info['section_name'])
                        
                        # Track length-wise quantities
                        length = component.length
                        nos = component.nos
                        
                        if length not in pipes_data[pipe_key]['lengths']:
                            pipes_data[pipe_key]['lengths'][length] = 0
                        
                        pipes_data[pipe_key]['lengths'][length] += nos
                        pipes_data[pipe_key]['total_meters'] += component.total_length
                        pipes_data[pipe_key]['total_nos'] += nos
        
        if not pipes_data:
            ws.write(row, 0, 'No pipe data available', styles['data'])
            return
        
        # Get all unique lengths across all pipes
        all_lengths = set()
        for pipe_data in pipes_data.values():
            all_lengths.update(pipe_data['lengths'].keys())
        
        sorted_lengths = sorted(all_lengths)
        
        # Calculate column positions
        base_cols = 4  # Pipe Type, Size, WT, Rate/Kg
        length_cols = len(sorted_lengths)
        total_qty_col = base_cols + length_cols
        total_nos_col = total_qty_col + 1
        used_in_col = total_nos_col + 1
        
        # Set column widths
        ws.set_column('A:A', 15)  # Pipe Type
        ws.set_column('B:B', 12)  # Size
        ws.set_column('C:C', 10)  # WT
        ws.set_column('D:D', 12)  # Rate/Kg
        
        # Length columns
        for i in range(length_cols):
            col_letter = chr(ord('E') + i)
            ws.set_column(f'{col_letter}:{col_letter}', 12)
        
        # Total columns
        total_qty_letter = chr(ord('E') + length_cols)
        total_nos_letter = chr(ord('E') + length_cols + 1)
        used_in_letter = chr(ord('E') + length_cols + 2)
        
        ws.set_column(f'{total_qty_letter}:{total_qty_letter}', 15)
        ws.set_column(f'{total_nos_letter}:{total_nos_letter}', 12)
        ws.set_column(f'{used_in_letter}:{used_in_letter}', 25)
        
        # Headers - Row 1
        ws.write(row, 0, 'Pipe Type', styles['header'])
        ws.write(row, 1, 'Size (mm)', styles['header'])
        ws.write(row, 2, 'WT (mm)', styles['header'])
        ws.write(row, 3, 'Rate/Kg', styles['header'])
        
        # Length-wise quantity headers
        col_idx = 4
        for length in sorted_lengths:
            ws.write(row, col_idx, f'{length}m (nos)', styles['header'])
            col_idx += 1
        
        ws.write(row, total_qty_col, 'Total Qty (m)', styles['header'])
        ws.write(row, total_nos_col, 'Total Nos', styles['header'])
        ws.write(row, used_in_col, 'Used In Sections', styles['header'])
        row += 1
        
        # Data rows
        for pipe_key in sorted(pipes_data.keys()):
            pipe_data = pipes_data[pipe_key]
            
            ws.write(row, 0, pipe_data['type'], styles['data'])
            ws.write(row, 1, pipe_data['size'], styles['data_center'])
            ws.write(row, 2, pipe_data['wt'], styles['data_center'])
            ws.write(row, 3, round(pipe_data['rate'], 2), styles['currency'])
            
            # Length-wise quantities
            col_idx = 4
            for length in sorted_lengths:
                qty = pipe_data['lengths'].get(length, 0)
                if qty > 0:
                    ws.write(row, col_idx, qty, styles['data_center'])
                else:
                    ws.write(row, col_idx, '-', styles['data_center'])
                col_idx += 1
            
            # Total quantity in meters
            ws.write(row, total_qty_col, round(pipe_data['total_meters'], 2), styles['data_right'])
            
            # Total number of pieces
            ws.write(row, total_nos_col, pipe_data['total_nos'], styles['data_center'])
            
            # Used in sections
            ws.write(row, used_in_col, ', '.join(sorted(pipe_data['sections'])), styles['data'])
            
            row += 1
        
        # Summary section
        row += 2
        ws.write(row, 0, 'SUMMARY:', styles['subheader'])
        row += 1
        
        total_unique_pipes = len(pipes_data)
        total_all_meters = sum(p['total_meters'] for p in pipes_data.values())
        total_all_pieces = sum(p['total_nos'] for p in pipes_data.values())
        
        ws.write(row, 0, 'Total Unique Pipe Types:', styles['data'])
        ws.write(row, 1, total_unique_pipes, styles['data_center'])
        row += 1
        
        ws.write(row, 0, 'Total Meters (All Pipes):', styles['data'])
        ws.write(row, 1, round(total_all_meters, 2), styles['data_right'])
        row += 1
        
        ws.write(row, 0, 'Total Pieces (All Pipes):', styles['data'])
        ws.write(row, 1, total_all_pieces, styles['data_center'])
        row += 1
        
        # Length-wise summary
        row += 1
        ws.write(row, 0, 'LENGTH-WISE SUMMARY:', styles['subheader'])
        row += 1
        
        ws.write(row, 0, 'Length', styles['header'])
        ws.write(row, 1, 'Total Pieces', styles['header'])
        ws.write(row, 2, 'Total Meters', styles['header'])
        row += 1
        
        # Calculate length-wise totals
        length_totals = {}
        for pipe_data in pipes_data.values():
            for length, qty in pipe_data['lengths'].items():
                if length not in length_totals:
                    length_totals[length] = {'pieces': 0, 'meters': 0}
                length_totals[length]['pieces'] += qty
                length_totals[length]['meters'] += (length * qty)
        
        for length in sorted(length_totals.keys()):
            ws.write(row, 0, f'{length} m', styles['data'])
            ws.write(row, 1, length_totals[length]['pieces'], styles['data_center'])
            ws.write(row, 2, round(length_totals[length]['meters'], 2), styles['data_right'])
            row += 1