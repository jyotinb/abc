# -*- coding: utf-8 -*-
from odoo.addons.green2_base.controllers.green_excel_export import GreenhouseExcelExport
import logging

_logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# AUTO-REGISTER DOORS COMPONENTS TO EXCEL EXPORT
# ═══════════════════════════════════════════════════════════════
GreenhouseExcelExport.register_component_section('door_component_ids', {
    'sheet_name': 'Doors Components',
    'section_name': 'DOORS',
    'cost_field': 'total_door_cost',
    'priority': 35,
    'is_accessory': False  # Change to True if doors don't have pipe data
})

_logger.info("✅ Doors module registered for Excel export")