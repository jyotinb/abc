from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re



class GreenhouseType(models.Model):
    _name = 'greenhouse.type'
    _description = 'Greenhouse Type Configuration'
    _order = 'sequence, name'

    name = fields.Char(string='Type Name', required=True, help='e.g., NVPH, Tunnel')
    code = fields.Char(string='Code', required=True, help='Unique identifier')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Section configuration
    section_ids = fields.One2many(
        'greenhouse.type.section', 'greenhouse_type_id', 
        string='Sections', help='Sections included in this greenhouse type'
    )
    
    @api.constrains('section_ids')
    def _check_section_dependencies(self):
        """Validate that section dependencies are satisfied"""
        for record in self:
            if not record.section_ids:
                continue
                
            available_sections = set(record.section_ids.mapped('section_id.code'))
            
            for type_section in record.section_ids:
                section = type_section.section_id
                dependencies = self._get_section_dependencies(section)
                
                missing_deps = dependencies - available_sections
                if missing_deps:
                    raise ValidationError(
                        f"Section '{section.name}' requires sections: {', '.join(missing_deps)}. "
                        f"Please add the required sections first."
                    )
    
    def _get_section_dependencies(self, section):
        """Extract section dependencies from field formulas"""
        dependencies = set()
        
        for field in section.calculated_field_ids:
            if field.formula:
                # Find all section.field references in formula
                matches = re.findall(r'(\w+)\.(\w+)', field.formula)
                for section_code, field_code in matches:
                    dependencies.add(section_code)
        
        # Remove self-reference
        dependencies.discard(section.code)
        return dependencies


class GreenhouseTypeSection(models.Model):
    _name = 'greenhouse.type.section'
    _description = 'Greenhouse Type Section Link'
    _order = 'sequence, section_id'

    greenhouse_type_id = fields.Many2one('greenhouse.type', required=True, ondelete='cascade')
    section_id = fields.Many2one('greenhouse.section.template', required=True)
    sequence = fields.Integer(string='Display Order', default=10)
    
    _sql_constraints = [
        ('unique_type_section', 'unique(greenhouse_type_id, section_id)', 
         'Section can only be added once per greenhouse type!')
    ]
