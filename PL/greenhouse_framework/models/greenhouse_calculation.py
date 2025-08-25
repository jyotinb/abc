# -*- coding: utf-8 -*-
"""
Greenhouse Calculation Engine
Handles inter-section dependencies using topological sort
"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import defaultdict, deque
import json
import re
import math
import logging

_logger = logging.getLogger(__name__)


class CalculationEngine:
    """Core calculation engine with dependency resolution"""
    
    def __init__(self, project):
        self.project = project
        self.input_values = {}
        self.calculated_values = {}
        self.formulas = {}
        self.dependencies = defaultdict(set)
        self.dependents = defaultdict(set)
        self.section_map = {}
        
        # Load all input values
        self._load_input_values()
    
    def _load_input_values(self):
        """Load all input values from the project"""
        for input_val in self.project.input_value_ids:
            self.input_values[input_val.field_code] = input_val.get_typed_value()
        
        # Add computed dimension values
        self._compute_basic_dimensions()
    
    def _compute_basic_dimensions(self):
        """Compute basic dimensions that other calculations depend on"""
        # Calculate span_length and bay_length
        self.input_values['span_length'] = (
            self.input_values.get('total_span_length', 0) - 
            self.input_values.get('width_front_span_coridoor', 0) - 
            self.input_values.get('width_back_span_coridoor', 0)
        )
        
        self.input_values['bay_length'] = (
            self.input_values.get('total_bay_length', 0) - 
            self.input_values.get('width_front_bay_coridoor', 0) - 
            self.input_values.get('width_back_bay_coridoor', 0)
        )
        
        # Calculate number of spans and bays
        span_width = self.input_values.get('span_width', 1)
        bay_width = self.input_values.get('bay_width', 1)
        
        self.input_values['no_of_spans'] = int(self.input_values['bay_length'] / span_width) if span_width > 0 else 0
        self.input_values['no_of_bays'] = int(self.input_values['span_length'] / bay_width) if bay_width > 0 else 0
        
        # Structure size
        self.input_values['structure_size'] = (
            (self.input_values['span_length'] + 
             self.input_values.get('width_front_span_coridoor', 0) + 
             self.input_values.get('width_back_span_coridoor', 0)) *
            (self.input_values['bay_length'] + 
             self.input_values.get('width_front_bay_coridoor', 0) + 
             self.input_values.get('width_back_bay_coridoor', 0))
        )
    
    def add_formula(self, code, formula_dict, section):
        """Add a formula and extract its dependencies"""
        self.formulas[code] = formula_dict
        self.section_map[code] = section
        
        formula = formula_dict.get('formula', '')
        
        # Extract dependencies - look for CALC('xxx') or CALC("xxx")
        calc_pattern = r"CALC\(['\"]([^'\"]+)['\"][,\)]"
        dependencies = re.findall(calc_pattern, formula)
        
        # Also check for direct variable references in complex formulas
        var_pattern = r"\b([A-Z_]+[A-Z0-9_]*)\b"
        potential_vars = re.findall(var_pattern, formula)
        
        for var in potential_vars:
            if var in ['GET', 'INT', 'CEIL', 'FLOOR', 'ABS', 'MIN', 'MAX', 'SUM']:
                continue  # Skip function names
            if var in self.formulas or var in dependencies:
                dependencies.append(var)
        
        # Remove duplicates
        dependencies = list(set(dependencies))
        
        for dep in dependencies:
            self.dependencies[code].add(dep)
            self.dependents[dep].add(code)
    
    def calculate_all(self):
        """Calculate all formulas in dependency order"""
        # Perform topological sort
        calculation_order = self._topological_sort()
        
        # Calculate in order
        results = []
        for code in calculation_order:
            if code in self.formulas:
                formula_dict = self.formulas[code]
                section = self.section_map[code]
                
                try:
                    value = self._evaluate_formula(formula_dict['formula'])
                    self.calculated_values[code] = value
                    
                    # Calculate length if specified
                    length = 0
                    length_formula = formula_dict.get('length_per_unit', '0')
                    if length_formula and str(length_formula) != '0':
                        length = self._evaluate_formula(str(length_formula))
                    
                    results.append({
                        'code': code,
                        'name': formula_dict.get('name', code),
                        'value': value,
                        'length': length,
                        'section': section,
                        'formula_dict': formula_dict
                    })
                    
                    _logger.info(f"Calculated {code}: {value} (length: {length})")
                    
                except Exception as e:
                    _logger.error(f"Error calculating {code}: {str(e)}")
                    results.append({
                        'code': code,
                        'name': f"ERROR: {formula_dict.get('name', code)}",
                        'value': 0,
                        'length': 0,
                        'section': section,
                        'formula_dict': formula_dict,
                        'error': str(e)
                    })
        
        return results
    
    def _topological_sort(self):
        """Perform topological sort to get calculation order"""
        # Count incoming edges for each node
        in_degree = {}
        all_nodes = set(self.formulas.keys())
        
        for node in all_nodes:
            in_degree[node] = len(self.dependencies.get(node, set()))
        
        # Find nodes with no dependencies
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        calculation_order = []
        
        while queue:
            current = queue.popleft()
            calculation_order.append(current)
            
            # Reduce in-degree for dependent nodes
            for dependent in self.dependents.get(current, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        # Check for circular dependencies
        if len(calculation_order) < len(all_nodes):
            remaining = [node for node in all_nodes if node not in calculation_order]
            raise ValidationError(
                f"Circular dependency detected in calculations: {remaining}\n"
                f"Check formulas for: {', '.join(remaining[:5])}"
            )
        
        return calculation_order
    
    def _evaluate_formula(self, formula):
        """Evaluate a formula with access to all values"""
        if not formula or formula == '0':
            return 0
        
        # Helper functions available in formulas
        def GET(key, default=0):
            return self.input_values.get(key, default)
        
        def CALC(key, default=0):
            return self.calculated_values.get(key, default)
        
        def INT(x):
            try:
                return int(float(x)) if x is not None else 0
            except:
                return 0
        
        def CEIL(x):
            try:
                return math.ceil(float(x)) if x is not None else 0
            except:
                return 0
        
        def FLOOR(x):
            try:
                return math.floor(float(x)) if x is not None else 0
            except:
                return 0
        
        # Replace variable references with calculated values
        # This handles direct variable references in formulas
        for var_name, var_value in self.calculated_values.items():
            # Only replace if it's a standalone variable (not part of a function call)
            pattern = r'\b' + var_name + r'\b(?!\s*\()'
            if re.search(pattern, formula):
                formula = re.sub(pattern, str(var_value), formula)
        
        # Evaluation context
        eval_context = {
            'GET': GET,
            'CALC': CALC,
            'INT': INT,
            'CEIL': CEIL,
            'FLOOR': FLOOR,
            'ABS': abs,
            'MIN': min,
            'MAX': max,
            'SUM': sum,
            'math': math,
            'True': True,
            'False': False,
        }
        
        try:
            # Safely evaluate the formula
            result = eval(formula, {"__builtins__": {}}, eval_context)
            return float(result) if result is not None else 0
        except Exception as e:
            _logger.error(f"Error evaluating formula '{formula}': {str(e)}")
            raise


class GreenhouseProject(models.Model):
    _inherit = 'greenhouse.project'
    
    def action_calculate(self):
        """Main calculation entry point"""
        self.ensure_one()
        
        try:
            # Clear existing results
            self.component_result_ids.unlink()
            
            # Initialize calculation engine
            engine = CalculationEngine(self)
            
            # Load all calculation rules from sections
            self._load_calculation_rules(engine)
            
            # Also load global calculations if they exist
            self._load_global_calculations(engine)
            
            # Perform calculations
            results = engine.calculate_all()
            
            # Create component result records
            self._create_component_results(results)
            
            # Update project status
            self.write({
                'state': 'calculated',
                'calculation_date': fields.Datetime.now(),
                'needs_recalculation': False,
            })
            
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Successfully calculated {len(results)} components!',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Calculation failed: {str(e)}")
            raise ValidationError(f"Calculation failed: {str(e)}")
    
    def _load_calculation_rules(self, engine):
        """Load calculation rules from active sections"""
        for section in self.active_section_ids.sorted('sequence'):
            rules = section.get_calculation_rules()
            for rule in rules:
                engine.add_formula(rule['code'], rule, section)
    
    def _load_global_calculations(self, engine):
        """Load global calculations from system parameter"""
        calc_json = self.env['ir.config_parameter'].sudo().get_param('greenhouse.calculation.variables')
        if calc_json:
            try:
                calculations = json.loads(calc_json)
                # Create a dummy section for global calculations
                global_section = self.env['greenhouse.section.template'].browse()
                
                for code, formula in calculations.items():
                    # Convert to rule format
                    rule = {
                        'code': code,
                        'name': code.replace('_', ' ').title(),
                        'formula': formula,
                        'sequence': 1000,  # Put global calculations last
                    }
                    
                    # Try to find which section this belongs to
                    for section in self.active_section_ids:
                        if self._belongs_to_section(code, section.code):
                            engine.add_formula(code, rule, section)
                            break
                    else:
                        # If no section found, use first section as default
                        if self.active_section_ids:
                            engine.add_formula(code, rule, self.active_section_ids[0])
                            
            except json.JSONDecodeError:
                _logger.error("Invalid JSON in global calculations")
    
    def _belongs_to_section(self, code, section_code):
        """Determine if a calculation code belongs to a section"""
        code_lower = code.lower()
        
        section_keywords = {
            'frame': ['column', 'frame', 'anchor'],
            'truss': ['arch', 'chord', 'v_support', 'purlin'],
            'asc': ['hockey', 'coridoor', 'corridor', 'asc'],
            'side_screen': ['screen', 'guard', 'curtain', 'rollup'],
            'gutter': ['gutter', 'funnel', 'drainage', 'ippf'],
            'lower': ['bracing', 'cross'],
        }
        
        keywords = section_keywords.get(section_code, [])
        return any(keyword in code_lower for keyword in keywords)
    
    def _create_component_results(self, results):
        """Create component result records from calculations"""
        for result in results:
            if result['value'] > 0 and 'error' not in result:
                self.env['greenhouse.component.result'].create({
                    'project_id': self.id,
                    'section_id': result['section'].id if result['section'] else False,
                    'name': result['name'],
                    'description': result['formula_dict'].get('description', ''),
                    'sequence': result['formula_dict'].get('sequence', 10),
                    'quantity': result['value'],
                    'length': result.get('length', 0),
                    'formula_used': result['formula_dict'].get('formula', ''),
                    'pipe_type': result['formula_dict'].get('pipe_type', ''),
                    'pipe_size': result['formula_dict'].get('pipe_size', ''),
                })
            elif 'error' in result:
                # Create error record
                self.env['greenhouse.component.result'].create({
                    'project_id': self.id,
                    'section_id': result['section'].id if result['section'] else False,
                    'name': result['name'],
                    'description': f"Calculation error: {result['error']}",
                    'sequence': result['formula_dict'].get('sequence', 10),
                    'quantity': 0,
                    'length': 0,
                    'formula_used': f"ERROR: {result['formula_dict'].get('formula', '')}",
                })