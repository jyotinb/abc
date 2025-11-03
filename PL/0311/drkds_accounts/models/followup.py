from odoo import models, fields

class Followup(models.Model):
    _name = 'drkds.followup'
    _description = 'Payment Follow-up'
    
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    level_ids = fields.One2many('drkds.followup.level', 'followup_id', 'Follow-up Levels')
    active = fields.Boolean(default=True)

class FollowupLevel(models.Model):
    _name = 'drkds.followup.level'
    _description = 'Follow-up Level'
    _order = 'delay'
    
    followup_id = fields.Many2one('drkds.followup', 'Follow-up', required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    delay = fields.Integer('Days Overdue', required=True)
    send_email = fields.Boolean('Send Email', default=True)
    description = fields.Html('Message')
