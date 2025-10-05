# Create a new file: PL/2909/green2/wizard/__init__.py
# -*- encoding: utf-8 -*-
from . import bulk_pipe_assignment_wizard

# Create a new file: PL/2909/green2/wizard/bulk_pipe_assignment_wizard.py
# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class BulkPipeAssignmentWizard(models.TransientModel):
    _name = 'bulk.pipe.assignment.wizard'
    _description = 'Bulk Pipe Assignment Wizard for Unassigned Components'
    
    green_master_id = fields.Many2one('green.master', string='Project', required=True)
    
    # Pipe selection fields
    pipe_id = fields.Many2one('pipe.management', string='Select Pipe to Assign', required=False,
                              help="This pipe will be assigned to all selected unassigned components")
    
    # Component selection
    component_line_ids = fields.Many2many(
        'component.line',
        'bulk_pipe_assignment_component_rel',
        'wizard_id',
        'component_id',
        string='Unassigned Components',
        domain="[('green_master_id', '=', green_master_id), ('pipe_id', '=', False)]"
    )
    
    # Filter fields
    filter_by_section = fields.Boolean(string='Filter by Section', default=False)
    section_filter = fields.Selection([
        ('asc', 'ASC Components'),
        ('frame', 'Frame Components'), 
        ('truss', 'Truss Components'),
        ('side_screen', 'Side Screen Components'),
        ('lower', 'Lower Section Components'),
    ], string='Section to Filter')
    
    filter_by_name_pattern = fields.Boolean(string='Filter by Name Pattern', default=False)
    name_pattern = fields.Char(string='Component Name Contains', 
                               help="Enter text to filter components by name (case insensitive)")
    
    # Statistics
    total_unassigned = fields.Integer(string='Total Unassigned', compute='_compute_statistics')
    selected_count = fields.Integer(string='Selected Count', compute='_compute_statistics')
    estimated_cost = fields.Float(string='Estimated Total Cost', compute='_compute_statistics')
    
    # Display fields from selected pipe
    pipe_display_info = fields.Text(string='Pipe Information', compute='_compute_pipe_info')
    
    @api.depends('green_master_id')
    def _compute_statistics(self):
        for wizard in self:
            if wizard.green_master_id:
                # Count total unassigned
                unassigned_components = self.env['component.line'].search([
                    ('green_master_id', '=', wizard.green_master_id.id),
                    ('pipe_id', '=', False)
                ])
                wizard.total_unassigned = len(unassigned_components)
                wizard.selected_count = len(wizard.component_line_ids)
                
                # Calculate estimated cost if pipe is selected
                if wizard.pipe_id and wizard.component_line_ids:
                    total_cost = 0
                    for component in wizard.component_line_ids:
                        total_length = component.nos * component.length
                        total_weight = total_length * (wizard.pipe_id.weight or 0)
                        total_cost += total_weight * (wizard.pipe_id.rate or 0)
                    wizard.estimated_cost = total_cost
                else:
                    wizard.estimated_cost = 0.0
            else:
                wizard.total_unassigned = 0
                wizard.selected_count = 0
                wizard.estimated_cost = 0.0
    
    @api.depends('pipe_id')
    def _compute_pipe_info(self):
        for wizard in self:
            if wizard.pipe_id:
                info_lines = [
                    f"Type: {wizard.pipe_id.name.name if wizard.pipe_id.name else 'N/A'}",
                    f"Size: {wizard.pipe_id.pipe_size.size_in_mm if wizard.pipe_id.pipe_size else 0} mm",
                    f"Wall Thickness: {wizard.pipe_id.wall_thickness.thickness_in_mm if wizard.pipe_id.wall_thickness else 0} mm",
                    f"Weight: {wizard.pipe_id.weight or 0} kg/m",
                    f"Rate: {wizard.pipe_id.rate or 0} per kg",
                ]
                wizard.pipe_display_info = "\n".join(info_lines)
            else:
                wizard.pipe_display_info = "No pipe selected"
    
    @api.onchange('filter_by_section', 'section_filter', 'filter_by_name_pattern', 'name_pattern')
    def _onchange_filters(self):
        """Apply filters to the component selection"""
        if self.green_master_id:
            domain = [
                ('green_master_id', '=', self.green_master_id.id),
                ('pipe_id', '=', False)
            ]
            
            if self.filter_by_section and self.section_filter:
                domain.append(('section', '=', self.section_filter))
            
            if self.filter_by_name_pattern and self.name_pattern:
                domain.append(('name', 'ilike', self.name_pattern))
            
            # Update domain for component_line_ids field
            filtered_components = self.env['component.line'].search(domain)
            self.component_line_ids = [(6, 0, filtered_components.ids)]
            
            return {
                'domain': {
                    'component_line_ids': domain
                }
            }
    
    def action_apply_quick_filters(self):
        """Quick filter actions"""
        return True
    
    def action_select_all_unassigned(self):
        """Select all unassigned components"""
        if self.green_master_id:
            domain = [
                ('green_master_id', '=', self.green_master_id.id),
                ('pipe_id', '=', False)
            ]
            
            if self.filter_by_section and self.section_filter:
                domain.append(('section', '=', self.section_filter))
            
            if self.filter_by_name_pattern and self.name_pattern:
                domain.append(('name', 'ilike', self.name_pattern))
            
            unassigned_components = self.env['component.line'].search(domain)
            self.component_line_ids = [(6, 0, unassigned_components.ids)]
    
    def action_clear_selection(self):
        """Clear all selected components"""
        self.component_line_ids = [(5, 0, 0)]
    
    def action_assign_pipes(self):
        """Assign the selected pipe to all selected components"""
        if not self.component_line_ids:
            raise UserError(_('Please select at least one component to assign pipes.'))
        
        if not self.pipe_id:
            raise UserError(_('Please select a pipe to assign to the components.'))
        
        # Perform the assignment
        assigned_count = 0
        failed_assignments = []
        
        for component in self.component_line_ids:
            try:
                component.pipe_id = self.pipe_id.id
                assigned_count += 1
            except Exception as e:
                failed_assignments.append(f"{component.name}: {str(e)}")
                _logger.error(f"Failed to assign pipe to component {component.name}: {e}")
        
        # Prepare result message
        if assigned_count > 0 and not failed_assignments:
            message = _(f"Successfully assigned {self.pipe_id.display_name} to {assigned_count} components.")
            message_type = 'success'
        elif assigned_count > 0 and failed_assignments:
            message = _(f"Assigned pipe to {assigned_count} components. Failed: {', '.join(failed_assignments[:3])}")
            message_type = 'warning'
        else:
            message = _("Failed to assign pipes to any components.")
            message_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Pipe Assignment'),
                'message': message,
                'type': message_type,
                'sticky': True,
            }
        }
    
    def action_assign_and_close(self):
        """Assign pipes and close the wizard"""
        self.action_assign_pipes()
        return {'type': 'ir.actions.act_window_close'}
    
    def action_preview_assignment(self):
        """Preview the components that will be affected"""
        if not self.component_line_ids:
            raise UserError(_('No components selected for preview.'))
        
        # Create a tree view of selected components
        return {
            'name': _('Components to be Assigned'),
            'type': 'ir.actions.act_window',
            'res_model': 'component.line',
            'view_mode': 'tree',
            'domain': [('id', 'in', self.component_line_ids.ids)],
            'target': 'new',
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            }
        }


class GreenMaster(models.Model):
    _inherit = 'green.master'
    
    def action_open_bulk_pipe_assignment(self):
        """Open the bulk pipe assignment wizard"""
        # Count unassigned components
        unassigned_count = self.env['component.line'].search_count([
            ('green_master_id', '=', self.id),
            ('pipe_id', '=', False)
        ])
        
        if unassigned_count == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Unassigned Components'),
                    'message': _('All components already have pipes assigned!'),
                    'type': 'info',
                }
            }
        
        # Create and open wizard
        wizard = self.env['bulk.pipe.assignment.wizard'].create({
            'green_master_id': self.id,
        })
        
        return {
            'name': _('Bulk Pipe Assignment - %s Unassigned Components') % unassigned_count,
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.pipe.assignment.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_green_master_id': self.id,
            }
        }
    
    def action_auto_assign_pipes_by_pattern(self):
        """Smart auto-assignment based on component name patterns"""
        # This method can be extended to implement intelligent pipe assignment
        # based on component naming patterns or historical data
        
        assignment_rules = {
            # Pattern matching for automatic assignment
            'Column': {'size': 100, 'thickness': 3.0},  # Example rule
            'Arch': {'size': 76, 'thickness': 2.0},
            'Purlin': {'size': 50, 'thickness': 2.0},
            'Support': {'size': 42, 'thickness': 2.0},
            'Bracing': {'size': 33, 'thickness': 1.5},
            'Guard': {'size': 25, 'thickness': 1.5},
        }
        
        unassigned_components = self.env['component.line'].search([
            ('green_master_id', '=', self.id),
            ('pipe_id', '=', False)
        ])
        
        assigned_count = 0
        for component in unassigned_components:
            for pattern, specs in assignment_rules.items():
                if pattern.lower() in component.name.lower():
                    # Try to find a matching pipe
                    matching_pipe = self.env['pipe.management'].search([
                        ('pipe_size.size_in_mm', '=', specs['size']),
                        ('wall_thickness.thickness_in_mm', '=', specs['thickness']),
                    ], limit=1)
                    
                    if matching_pipe:
                        component.pipe_id = matching_pipe.id
                        assigned_count += 1
                        break
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-Assignment Complete'),
                'message': _(f'Automatically assigned pipes to {assigned_count} components based on naming patterns.'),
                'type': 'success' if assigned_count > 0 else 'info',
            }
        }
    
    @api.model
    def get_unassigned_components_summary(self):
        """Get summary of unassigned components by section"""
        summary = {}
        
        for project in self:
            unassigned = self.env['component.line'].search([
                ('green_master_id', '=', project.id),
                ('pipe_id', '=', False)
            ])
            
            section_summary = {}
            for component in unassigned:
                if component.section not in section_summary:
                    section_summary[component.section] = {
                        'count': 0,
                        'components': []
                    }
                section_summary[component.section]['count'] += 1
                section_summary[component.section]['components'].append(component.name)
            
            summary[project.id] = {
                'project_name': project.customer,
                'total_unassigned': len(unassigned),
                'by_section': section_summary
            }
        
        return summary