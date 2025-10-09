from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BulkPipeWizard(models.TransientModel):
    _name = 'greenhouse.bulk.pipe.wizard'
    _description = 'Bulk Pipe Assignment'
    
    project_id = fields.Many2one('greenhouse.project', 'Project', required=True)
    pipe_id = fields.Many2one('greenhouse.pipe.management', 'Pipe to Assign', required=True)
    component_ids = fields.Many2many('greenhouse.component.line', string='Components')
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('active_id'):
            project = self.env['greenhouse.project'].browse(self.env.context['active_id'])
            res['project_id'] = project.id
            unassigned = project.component_line_ids.filtered(lambda c: not c.pipe_id)
            res['component_ids'] = [(6, 0, unassigned.ids)]
        return res
    
    def action_assign(self):
        if not self.component_ids:
            raise UserError(_('Please select components'))
        
        self.component_ids.write({'pipe_id': self.pipe_id.id})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Assigned pipe to {len(self.component_ids)} components',
                'type': 'success',
            }
        }
