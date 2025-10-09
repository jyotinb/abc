from odoo import http
from odoo.http import request

class ExcelExport(http.Controller):
    @http.route('/greenhouse/export/<int:project_id>', type='http', auth='user')
    def export_excel(self, project_id):
        # Simplified Excel export
        return request.make_response(
            b"Excel export placeholder",
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=greenhouse.xlsx')
            ]
        )
