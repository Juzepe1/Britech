from odoo import api, Command, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_so_lines_new_project(self):
        return self.filtered(lambda sol: sol.product_id.service_tracking in ['project_only', 'task_in_project'])
