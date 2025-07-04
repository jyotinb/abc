# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re
from datetime import datetime

class ComplianceChecker(models.Model):
    _name = 'email.compliance.checker'
    _description = 'Email Compliance & Anti-Spam Checker'

    name = fields.Char('Check Name', required=True)
    template_id = fields.Many2one('email.marketing.template', string='Template')
    
    # Compliance scores
    overall_score = fields.Float('Overall Compliance Score', readonly=True)
    spam_score = fields.Float('Spam Risk Score', readonly=True)
    gdpr_score = fields.Float('GDPR Compliance Score', readonly=True)
    can_spam_score = fields.Float('CAN-SPAM Compliance Score', readonly=True)
    
    # Detailed checks
    has_unsubscribe_link = fields.Boolean('Has Unsubscribe Link', readonly=True)
    has_physical_address = fields.Boolean('Has Physical Address', readonly=True)
    has_clear_sender = fields.Boolean('Has Clear Sender', readonly=True)
    subject_line_quality = fields.Float('Subject Line Quality', readonly=True)
    content_quality = fields.Float('Content Quality Score', readonly=True)
    
    # Spam indicators
    spam_words_count = fields.Integer('Spam Words Found', readonly=True)
    excessive_caps = fields.Boolean('Excessive Capitalization', readonly=True)
    excessive_exclamation = fields.Boolean('Excessive Exclamation Marks', readonly=True)
    missing_alt_text = fields.Boolean('Missing Image Alt Text', readonly=True)
    
    # Recommendations
    recommendations = fields.Text('Compliance Recommendations', readonly=True)
    critical_issues = fields.Text('Critical Issues', readonly=True)
    
    # Check results
    check_date = fields.Datetime('Last Check Date', readonly=True)
    is_compliant = fields.Boolean('Fully Compliant', readonly=True)
    
    def run_compliance_check(self, template):
        """Run comprehensive compliance check"""
        self.template_id = template.id
        self.check_date = datetime.now()
        
        # Initialize scores
        spam_score = 100
        gdpr_score = 100
        can_spam_score = 100
        
        issues = []
        recommendations = []
        
        # Check basic compliance elements
        self._check_unsubscribe_link(template, issues, recommendations)
        self._check_physical_address(template, issues, recommendations)
        self._check_clear_sender(template, issues, recommendations)
        
        # Check spam indicators
        spam_score = self._check_spam_content(template, issues, recommendations)
        
        # Check subject line
        subject_score = self._check_subject_line(template, issues, recommendations)
        
        # Check content quality
        content_score = self._check_content_quality(template, issues, recommendations)
        
        # Calculate GDPR compliance
        gdpr_score = self._calculate_gdpr_score(template, issues, recommendations)
        
        # Calculate CAN-SPAM compliance
        can_spam_score = self._calculate_can_spam_score(template, issues, recommendations)
        
        # Calculate overall score
        overall_score = (spam_score + gdpr_score + can_spam_score + subject_score + content_score) / 5
        
        # Update record
        self.write({
            'overall_score': overall_score,
            'spam_score': spam_score,
            'gdpr_score': gdpr_score,
            'can_spam_score': can_spam_score,
            'subject_line_quality': subject_score,
            'content_quality': content_score,
            'recommendations': '\n'.join(recommendations),
            'critical_issues': '\n'.join(issues),
            'is_compliant': overall_score >= 80 and len([i for i in issues if 'CRITICAL' in i]) == 0,
        })
        
        return {
            'overall_score': overall_score,
            'is_compliant': self.is_compliant,
            'issues': issues,
            'recommendations': recommendations,
        }
    
    def _check_unsubscribe_link(self, template, issues, recommendations):
        """Check for unsubscribe link"""
        body = (template.body_html or '').lower()
        has_unsubscribe = 'unsubscribe' in body or '{{unsubscribe_url}}' in body
        
        self.has_unsubscribe_link = has_unsubscribe
        
        if not has_unsubscribe:
            issues.append('CRITICAL: Missing unsubscribe link')
            recommendations.append('Add unsubscribe link: {{unsubscribe_url}}')
        else:
            recommendations.append('✓ Unsubscribe link found')
    
    def _check_physical_address(self, template, issues, recommendations):
        """Check for physical address"""
        has_address = bool(template.company_address)
        body_has_address = '{{company_address}}' in (template.body_html or '')
        
        self.has_physical_address = has_address and body_has_address
        
        if not has_address:
            issues.append('CRITICAL: Missing company physical address')
            recommendations.append('Add company address in template settings')
        elif not body_has_address:
            issues.append('WARNING: Address not included in email body')
            recommendations.append('Include {{company_address}} in email footer')
        else:
            recommendations.append('✓ Physical address included')
    
    def _check_clear_sender(self, template, issues, recommendations):
        """Check for clear sender identification"""
        has_sender_name = bool(template.sender_name)
        has_sender_email = bool(template.sender_email)
        
        self.has_clear_sender = has_sender_name and has_sender_email
        
        if not has_sender_name:
            issues.append('CRITICAL: Missing sender name')
            recommendations.append('Set clear sender name')
        if not has_sender_email:
            issues.append('CRITICAL: Missing sender email')
            recommendations.append('Set valid sender email address')
        if has_sender_name and has_sender_email:
            recommendations.append('✓ Clear sender identification')
    
    def _check_spam_content(self, template, issues, recommendations):
        """Check for spam indicators in content"""
        body = (template.body_html or '').lower()
        score = 100
        
        # Common spam words
        spam_words = [
            'free', 'urgent', 'act now', 'limited time', 'click here', 'buy now',
            'order now', 'guaranteed', 'risk free', 'no obligation', 'winner',
        ]
        
        spam_count = 0
        for word in spam_words:
            if word in body:
                spam_count += body.count(word)
        
        self.spam_words_count = spam_count
        
        if spam_count > 0:
            score -= min(spam_count * 10, 50)
            recommendations.append(f'Reduce spam words (found {spam_count})')
        
        # Check excessive capitalization
        caps_ratio = sum(1 for c in template.subject if c.isupper()) / len(template.subject) if template.subject else 0
        self.excessive_caps = caps_ratio > 0.3
        
        if self.excessive_caps:
            score -= 15
            recommendations.append('Reduce excessive capitalization in subject')
        
        # Check excessive exclamation marks
        exclamation_count = (template.subject or '').count('!') + body.count('!')
        self.excessive_exclamation = exclamation_count > 3
        
        if self.excessive_exclamation:
            score -= 10
            recommendations.append('Reduce exclamation marks')
        
        return max(score, 0)
    
    def _check_subject_line(self, template, issues, recommendations):
        """Check subject line quality"""
        subject = template.subject or ''
        score = 100
        
        # Check length
        if len(subject) < 10:
            score -= 20
            recommendations.append('Subject line too short (min 10 characters)')
        elif len(subject) > 60:
            score -= 15
            recommendations.append('Subject line too long (max 60 characters recommended)')
        
        # Check for personalization
        if '{{partner_name}}' in subject or '{{company_name}}' in subject:
            score += 10
            recommendations.append('✓ Personalization found in subject')
        else:
            recommendations.append('Consider adding personalization to subject')
        
        return max(score, 0)
    
    def _check_content_quality(self, template, issues, recommendations):
        """Check overall content quality"""
        body = template.body_html or ''
        score = 100
        
        # Check text content length
        text_content = re.sub(r'<[^>]+>', '', body)
        text_length = len(text_content.strip())
        
        if text_length < 100:
            score -= 20
            recommendations.append('Add more text content (minimum 100 characters)')
        
        # Check for clear call-to-action
        cta_indicators = ['click', 'visit', 'shop', 'buy', 'learn more', 'get started']
        has_cta = any(indicator in body.lower() for indicator in cta_indicators)
        
        if not has_cta:
            score -= 10
            recommendations.append('Consider adding clear call-to-action')
        else:
            recommendations.append('✓ Call-to-action found')
        
        return max(score, 0)
    
    def _calculate_gdpr_score(self, template, issues, recommendations):
        """Calculate GDPR compliance score"""
        score = 100
        
        # Must have unsubscribe
        if not self.has_unsubscribe_link:
            score -= 40
        
        # Should have clear sender identification
        if not self.has_clear_sender:
            score -= 20
        
        return max(score, 0)
    
    def _calculate_can_spam_score(self, template, issues, recommendations):
        """Calculate CAN-SPAM compliance score"""
        score = 100
        
        # Must have unsubscribe
        if not self.has_unsubscribe_link:
            score -= 30
        
        # Must have physical address
        if not self.has_physical_address:
            score -= 30
        
        # Must have clear sender
        if not self.has_clear_sender:
            score -= 20
        
        return max(score, 0)
    
    def get_compliance_badge(self):
        """Get compliance badge based on score"""
        if self.overall_score >= 90:
            return {'badge': '🏆', 'text': 'Excellent', 'class': 'text-success'}
        elif self.overall_score >= 80:
            return {'badge': '✅', 'text': 'Good', 'class': 'text-info'}
        elif self.overall_score >= 60:
            return {'badge': '⚠️', 'text': 'Needs Improvement', 'class': 'text-warning'}
        else:
            return {'badge': '❌', 'text': 'Poor', 'class': 'text-danger'}
