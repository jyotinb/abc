# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TemplateBuilderWizard(models.TransientModel):
    _name = 'greenhouse.template.builder.wizard'
    _description = 'Greenhouse Template Builder Wizard'

    template_id = fields.Many2one('email.marketing.template', string='Template')
    template_name = fields.Char('Template Name', required=True)
    greenhouse_category = fields.Selection([
        ('general', 'General Greenhouse'),
        ('vegetables', 'Vegetable Growing'),
        ('flowers', 'Flower Production'),
        ('herbs', 'Herb Cultivation'),
        ('organic', 'Organic Farming'),
        ('automation', 'Smart Greenhouse'),
    ], string='Category', required=True)
    
    growing_season = fields.Selection([
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
        ('winter', 'Winter'),
        ('year_round', 'Year Round'),
    ], string='Season', required=True)
    
    def action_build_template(self):
        """Build template with greenhouse components"""
        # Template building logic will be implemented here
        return {'type': 'ir.actions.act_window_close'}
