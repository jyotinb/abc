# -*- coding: utf-8 -*-
from odoo import models, fields

class AccessoriesMasterNutbolts(models.Model):
    _inherit = 'accessories.master'
    
    category = fields.Selection(
        selection_add=[('nutbolts', 'Nut-Bolts & Screws')],
        ondelete={'nutbolts': 'cascade'}
    )