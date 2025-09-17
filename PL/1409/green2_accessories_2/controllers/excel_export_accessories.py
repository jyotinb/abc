# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.green2.controllers.green_excel_export import GreenhouseExcelExport
import logging

_logger = logging.getLogger(__name__)

class GreenhouseExcelExportAccessories(GreenhouseExcelExport):
    """Extend Excel export to include accessories"""
    
    def _create_additional_sheets(self, workbook, project, styles):
        """Override to add accessories worksheets"""
        # Call parent method first
        super()._create_additional_sheets(workbook, project, styles)
        
        # Add accessories sheets
        if hasattr(project, 'accessories_component_ids') and project.accessories_component_ids:
            self._create_accessories_summary_sheet(workbook, project, styles)
            self._create_accessories_detail_sheets(workbook, project, styles)
    
    def _create_accessories_summary_sheet(self, workbook, project, styles):
        """Create accessories summary worksheet"""
        ws = workbook.add_worksheet('Accessories Summary')
        ws.set_column('A:A', 30)
        ws.set_column('B:B', 15)
        ws.set_column('C:C', 15)
        ws.set_column('D:D', 15)
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 3, 'ACCESSORIES SUMMARY', styles['title'])
        row += 2
        
        # Configuration Summary
        ws.merge_range(row, 0, row, 3, 'CONFIGURATION', styles['header'])
        row += 1
        
        config_data = [
            ('Gutter Bracket Type:', dict(project._fields['gutter_bracket_type'].selection)[project.gutter_bracket_type]),
            ('Column Bracket Type:', dict(project._fields['column_bracket_type'].selection)[project.column_bracket_type]),
            ('Zigzag Wire:', 'Enabled (' + project.zigzag_wire_size + ')' if project.enable_zigzag_wire else 'Disabled'),
            ('Roll Up Connectors:', 'Enabled' if project.enable_rollup_connectors else 'Disabled'),
        ]
        
        for label, value in config_data:
            ws.write(row, 0, label, styles['subheader'])
            ws.write(row, 1, value, styles['data'])
            row += 1
        
        row += 1
        
        # Cost Summary
        ws.merge_range(row, 0, row, 3, 'COST BREAKDOWN', styles['header'])
        row += 1
        
        ws.write(row, 0, 'Category', styles['subheader'])
        ws.write(row, 1, 'Components', styles['subheader'])
        ws.write(row, 2, 'Total Cost', styles['subheader'])
        ws.write(row, 3, 'Percentage', styles['subheader'])
        row += 1
        
        cost_data = []
        if project.total_profiles_cost > 0:  # ADD THIS
            cost_data.append(('Profiles', len(project.profiles_component_ids), project.total_profiles_cost))
        if project.total_brackets_cost > 0:
            cost_data.append(('Brackets', len(project.brackets_component_ids), project.total_brackets_cost))
        if project.total_wires_connectors_cost > 0:
            cost_data.append(('Wires & Connectors', len(project.wires_connectors_component_ids), project.total_wires_connectors_cost))
        if project.total_clamps_cost > 0:
            cost_data.append(('Clamps', len(project.clamps_component_ids), project.total_clamps_cost))
        if project.total_foundation_cost > 0:  # ADD THIS LINE
            cost_data.append(('Foundation', len(project.foundation_component_ids), project.total_foundation_cost))
        
        for category, count, cost in cost_data:
            percentage = (cost / project.total_accessories_cost * 100) if project.total_accessories_cost > 0 else 0
            ws.write(row, 0, category, styles['data'])
            ws.write(row, 1, count, styles['data_center'])
            ws.write(row, 2, cost, styles['currency'])
            ws.write(row, 3, f"{round(percentage, 1)}%", styles['data_center'])
            row += 1
        
        # Total
        ws.write(row, 0, 'TOTAL ACCESSORIES', styles['total'])
        ws.write(row, 1, len(project.accessories_component_ids), styles['total'])
        ws.write(row, 2, project.total_accessories_cost, styles['total'])
        ws.write(row, 3, '100.0%', styles['total'])
        
    def _create_accessories_detail_sheets(self, workbook, project, styles):
        """Create detailed accessories worksheets"""
        
        # Create individual sheets for each accessory type
        if project.brackets_component_ids:
            self._create_accessories_component_sheet(workbook, project, styles, 
                                       project.brackets_component_ids, 
                                       'Brackets Components', 
                                       project.total_brackets_cost)
        
        if project.foundation_component_ids:
            self._create_accessories_component_sheet(workbook, project, styles, 
                                       project.foundation_component_ids, 
                                       'Foundation Components', 
                                       project.total_foundation_cost)
        # Add other accessories as needed
        
       
        
    def _create_accessories_component_sheet(self, workbook, project, styles, components, sheet_name, section_total):
        """Create accessories component sheet with proper field handling"""
        if not components:
            return
            
        ws = workbook.add_worksheet(sheet_name)
        
        # Set column widths
        ws.set_column('A:A', 35)  # Component Name
        ws.set_column('B:B', 10)  # Nos
        ws.set_column('C:C', 15)  # Size/Type
        ws.set_column('D:D', 12)  # Unit Price
        ws.set_column('E:E', 15)  # Total Cost
        
        row = 0
        
        # Title
        ws.merge_range(row, 0, row, 4, f'{sheet_name.upper()}', styles['title'])
        row += 2
        
        # Headers
        headers = ['Component Name', 'Nos', 'Size/Type', 'Unit Price', 'Total Cost']
        
        for col, header in enumerate(headers):
            ws.write(row, col, header, styles['header'])
        row += 1
        
        # Component data
        total_cost = 0
        
        for component in components:
            ws.write(row, 0, component.name, styles['data'])
            ws.write(row, 1, component.nos, styles['data_center'])
            ws.write(row, 2, component.size_specification or 'N/A', styles['data_center'])
            ws.write(row, 3, round(component.unit_price, 2) if component.unit_price else 0, styles['data_right'])
            ws.write(row, 4, round(component.total_cost, 2), styles['currency'])
            
            total_cost += component.total_cost
            row += 1
        
        # Totals row
        ws.write(row, 0, 'SECTION TOTAL', styles['section_total'])
        ws.write(row, 1, '', styles['section_total'])
        ws.write(row, 2, '', styles['section_total'])
        ws.write(row, 3, '', styles['section_total'])
        ws.write(row, 4, round(section_total, 2), styles['section_total'])