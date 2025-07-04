# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ComplianceWizard(models.TransientModel):
    _name = 'email.compliance.wizard'
    _description = 'Email Compliance Wizard'

    template_id = fields.Many2one('email.marketing.template', string='Template', required=True)
    
    def action_check_compliance(self):
        """Run compliance check and show results"""
        if self.template_id:
            return self.template_id.action_run_compliance_check()
        return {'type': 'ir.actions.act_window_close'}
