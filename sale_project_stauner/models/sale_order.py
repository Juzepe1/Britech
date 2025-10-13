from odoo import api, Command, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_show_project_and_task_button(self):
        is_project_manager = self.env.user.has_group('project.group_project_manager')
        show_button_ids = self.env['sale.order.line']._read_group([
            ('order_id', 'in', self.ids),
            ('order_id.state', 'not in', ['draft', 'sent']),
            ('product_id.service_policy', '!=', False),
        ], aggregates=['order_id:array_agg'])[0][0]
        for order in self:
            order.show_project_button = order.id in show_button_ids and order.project_count
            order.show_task_button = order.show_project_button or order.tasks_count
            order.show_create_project_button = (
                    is_project_manager
                    and order.id in show_button_ids
                    and not order.project_count
            )
