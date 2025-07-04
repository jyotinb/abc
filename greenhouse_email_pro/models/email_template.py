# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class EmailTemplate(models.Model):
    _name = 'email.marketing.template'
    _description = 'Professional Email Marketing Template'
    _order = 'name'

    name = fields.Char('Template Name', required=True)
    subject = fields.Char('Email Subject', required=True)
    body_html = fields.Html('Email Content', required=True)
    
    # Template classification
    template_type = fields.Selection([
        ('newsletter', 'Newsletter'),
        ('promotional', 'Promotional'),
        ('announcement', 'Announcement'),
        ('welcome', 'Welcome'),
        ('seasonal', 'Seasonal Growing'),
        ('harvest', 'Harvest Alerts'),
        ('equipment', 'Equipment Maintenance'),
        ('weather', 'Weather Updates'),
        ('certification', 'Organic Certification'),
        ('automation', 'Automation Alerts'),
        ('custom', 'Custom Built'),
    ], string='Type', default='newsletter', required=True)
    
    # Greenhouse specialization
    greenhouse_category = fields.Selection([
        ('general', 'General Greenhouse'),
        ('vegetables', 'Vegetable Growing'),
        ('flowers', 'Flower Production'),
        ('herbs', 'Herb Cultivation'),
        ('organic', 'Organic Farming'),
        ('hydroponic', 'Hydroponic Systems'),
        ('automation', 'Smart Greenhouse'),
        ('nursery', 'Plant Nursery'),
        ('retail', 'Garden Center'),
        ('wholesale', 'Wholesale Grower'),
    ], string='Greenhouse Category', default='general')
    
    # Seasonal targeting
    growing_season = fields.Selection([
        ('spring', 'Spring Planting'),
        ('summer', 'Summer Growing'),
        ('fall', 'Fall Harvest'),
        ('winter', 'Winter Prep'),
        ('year_round', 'Year Round'),
    ], string='Growing Season', default='year_round')
    
    # Business targeting
    target_audience = fields.Selection([
        ('b2b', 'Business Customers'),
        ('b2c', 'Home Gardeners'),
        ('mixed', 'Mixed Audience'),
    ], string='Target Audience', default='mixed')
    
    # Template building
    component_ids = fields.Many2many('email.template.component', string='Components')
    is_built_template = fields.Boolean('Built with Template Builder', default=False)
    symbol_ids = fields.Many2many('greenhouse.symbol.library', string='Used Symbols')
    
    # Compliance
    compliance_score = fields.Float('Compliance Score', readonly=True)
    is_compliant = fields.Boolean('Anti-Spam Compliant', readonly=True)
    last_compliance_check = fields.Datetime('Last Compliance Check', readonly=True)
    
    # Sender information (enhanced for compliance)
    sender_name = fields.Char('Sender Name', required=True)
    sender_email = fields.Char('Sender Email', required=True)
    reply_to_email = fields.Char('Reply-To Email')
    company_address = fields.Text('Physical Address', required=True,
                                 help='Required for CAN-SPAM compliance')
    
    # Professional features
    active = fields.Boolean('Active', default=True)
    usage_count = fields.Integer('Times Used', default=0, readonly=True)
    last_used = fields.Datetime('Last Used', readonly=True)
    success_rate = fields.Float('Success Rate %', compute='_compute_success_rate', store=True)
    
    # Anti-spam features
    unsubscribe_required = fields.Boolean('Unsubscribe Link Required', default=True)
    gdpr_compliant = fields.Boolean('GDPR Compliant', default=True)
    can_spam_compliant = fields.Boolean('CAN-SPAM Compliant', default=True)
    
    # Relationships
    campaign_ids = fields.One2many('email.marketing.campaign', 'template_id', string='Campaigns')
    compliance_checks = fields.One2many('email.compliance.checker', 'template_id', string='Compliance Checks')
    
    @api.constrains('sender_email', 'reply_to_email')
    def _check_email_format(self):
        for record in self:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if record.sender_email and not re.match(email_pattern, record.sender_email):
                raise ValidationError("Invalid sender email format")
            if record.reply_to_email and not re.match(email_pattern, record.reply_to_email):
                raise ValidationError("Invalid reply-to email format")
    
    @api.depends('campaign_ids')
    def _compute_success_rate(self):
        for template in self:
            if template.campaign_ids:
                rates = []
                for campaign in template.campaign_ids:
                    # Combined success metric
                    if hasattr(campaign, 'open_rate') and hasattr(campaign, 'click_rate'):
                        success = (campaign.open_rate * 0.6) + (campaign.click_rate * 0.4)
                        rates.append(success)
                template.success_rate = sum(rates) / len(rates) if rates else 0.0
            else:
                template.success_rate = 0.0
    
    def action_run_compliance_check(self):
        """Run comprehensive compliance check"""
        checker = self.env['email.compliance.checker'].create({
            'name': f'Compliance Check - {self.name}',
            'template_id': self.id,
        })
        
        results = checker.run_compliance_check(self)
        
        # Update template compliance fields
        self.write({
            'compliance_score': results['overall_score'],
            'is_compliant': results['is_compliant'],
            'last_compliance_check': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Compliance Check Results',
            'res_model': 'email.compliance.checker',
            'res_id': checker.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def get_greenhouse_symbols(self, category=None):
        """Get greenhouse symbols for template"""
        domain = [('active', '=', True)]
        if category:
            domain.append(('category', '=', category))
        
        symbols = self.env['greenhouse.symbol.library'].search(domain)
        return {symbol.category: symbol.symbol for symbol in symbols}
    
    def get_rendered_body(self, partner=None):
        """Get email body with variables replaced"""
        body = self.body_html
        
        # Standard replacements
        if partner:
            body = body.replace('{{partner_name}}', partner.name or 'Valued Customer')
        else:
            body = body.replace('{{partner_name}}', 'Valued Customer')
        
        body = body.replace('{{company_name}}', self.env.company.name)
        body = body.replace('{{company_address}}', self.company_address)
        body = body.replace('{{sender_name}}', self.sender_name)
        
        # Add unsubscribe link
        if partner and hasattr(partner, 'unsubscribe_token'):
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            unsubscribe_url = f"{base_url}/mail/unsubscribe/{partner.unsubscribe_token}"
            body = body.replace('{{unsubscribe_url}}', unsubscribe_url)
        else:
            body = body.replace('{{unsubscribe_url}}', '#')
        
        return body
