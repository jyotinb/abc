from odoo import models, fields, api, _
from odoo.exceptions import UserError

class JobWorkType(models.Model):
    _name = 'job.work.type'
    _inherit = ['mail.thread']
    _description = 'Job Work Type'

    name = fields.Char('Name', required=True, tracking=True)
    code = fields.Char('Code', tracking=True)
    operation_ids = fields.One2many('job.work.operation', 'type_id', 'Operations')
    company_id = fields.Many2one('res.company', string='Company', 
        default=lambda self: self.env.company, tracking=True)

class JobWorkOperation(models.Model):
    _name = 'job.work.operation'
    _inherit = ['mail.thread']
    _description = 'Job Work Operation'

    name = fields.Char('Operation Name', required=True, tracking=True)
    type_id = fields.Many2one('job.work.type', 'Job Work Type', tracking=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', tracking=True)
    sequence = fields.Integer('Sequence')
    rate = fields.Float('Operation Rate', tracking=True)
    notes = fields.Text('Notes')
    company_id = fields.Many2one('res.company', string='Company', 
        default=lambda self: self.env.company, tracking=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_job_work = fields.Boolean('Is Job Work')
    job_work_type_id = fields.Many2one('job.work.type', 'Job Work Type')