from odoo import models, fields, api


class GreenhouseProject(models.Model):
    _name = 'greenhouse.project'
    _description = 'Greenhouse Project'
    _order = 'create_date desc'

    name = fields.Char(string='Project Name', required=True)
    greenhouse_type_id = fields.Many2one('greenhouse.type', string='Greenhouse Type', required=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'), 
        ('confirmed', 'Confirmed')
    ], default='draft', string='Status')
    
    # Project data
    input_data_ids = fields.One2many(
        'greenhouse.project.data', 'project_id',
        domain=[('field_type', '=', 'input')],
        string='Input Data'
    )
    calculated_data_ids = fields.One2many(
        'greenhouse.project.data', 'project_id',
        domain=[('field_type', '=', 'calculated')],
        string='Calculated Data'
    )
    
    # Computed info
    total_sections = fields.Integer(
        compute='_compute_project_stats', 
        string='Total Sections'
    )
    completed_inputs = fields.Integer(
        compute='_compute_project_stats',
        string='Completed Inputs'
    )
    total_inputs = fields.Integer(
        compute='_compute_project_stats',
        string='Total Inputs'
    )
    
    @api.depends('greenhouse_type_id', 'input_data_ids.value_char')
    def _compute_project_stats(self):
        for record in self:
            if record.greenhouse_type_id:
                record.total_sections = len(record.greenhouse_type_id.section_ids)
                
                # Count required inputs vs completed
                total_inputs = 0
                completed_inputs = 0
                
                for section_link in record.greenhouse_type_id.section_ids:
                    section = section_link.section_id
                    for field in section.input_field_ids:
                        total_inputs += 1
                        # Check if this field has data
                        data_record = record.input_data_ids.filtered(
                            lambda d: d.section_code == section.code and d.field_code == field.code
                        )
                        if data_record and data_record.get_value():
                            completed_inputs += 1
                
                record.total_inputs = total_inputs
                record.completed_inputs = completed_inputs
            else:
                record.total_sections = 0
                record.total_inputs = 0
                record.completed_inputs = 0
    
    @api.model
    def create(self, vals):
        """Auto-create input data fields when project is created"""
        project = super().create(vals)
        project._create_project_data_fields()
        return project
    
    def _create_project_data_fields(self):
        """Create data fields based on greenhouse type configuration"""
        if not self.greenhouse_type_id:
            return
            
        data_vals = []
        
        for section_link in self.greenhouse_type_id.section_ids:
            section = section_link.section_id
            
            # Create input field records
            for field in section.input_field_ids:
                data_vals.append({
                    'project_id': self.id,
                    'section_code': section.code,
                    'section_name': section.name,
                    'field_code': field.code,
                    'field_name': field.name,
                    'field_type': 'input',
                    'data_type': field.data_type,
                    'label': field.label,
                    'sequence': field.sequence,
                    'required': field.required,
                    'default_value': field.default_value,
                    'help': field.help,
                })
            
            # Create calculated field records  
            for field in section.calculated_field_ids:
                data_vals.append({
                    'project_id': self.id,
                    'section_code': section.code,
                    'section_name': section.name,
                    'field_code': field.code,
                    'field_name': field.name,
                    'field_type': 'calculated',
                    'data_type': field.data_type,
                    'label': field.label,
                    'sequence': field.sequence,
                    'formula': field.formula,
                })
        
        if data_vals:
            self.env['greenhouse.project.data'].create(data_vals)
    
    def action_calculate(self):
        """Trigger calculation of all calculated fields"""
        # This will be implemented in Phase 2
        self.state = 'calculated'
        return True
