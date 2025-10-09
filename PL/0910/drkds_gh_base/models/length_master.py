from odoo import models, fields, api

class LengthMaster(models.Model):
    _name = 'greenhouse.length.master'
    _description = 'Length Master'
    _order = 'length_value'
    
    name = fields.Char('Name', compute='_compute_name', store=True)
    length_value = fields.Float('Length (m)', required=True)
    active = fields.Boolean('Active', default=True)
    
    @api.depends('length_value')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.length_value}m"
