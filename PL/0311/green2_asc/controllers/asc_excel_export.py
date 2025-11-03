# -*- coding: utf-8 -*-
from odoo.addons.green2_base.controllers.green_excel_export import GreenhouseExcelExport
import logging

_logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# AUTO-REGISTER ASC COMPONENTS TO EXCEL EXPORT
# ═══════════════════════════════════════════════════════════════
GreenhouseExcelExport.register_component_section('asc_component_ids', {
    'sheet_name': 'ASC Components',
    'section_name': 'ASC',
    'cost_field': 'total_asc_cost',
    'priority': 5,
    'is_accessory': False
})

_logger.info("✅ ASC module registered for Excel export")