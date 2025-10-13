from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    stau_is_template = fields.Boolean(
        string="Stauner Project Template",
        help="If enabled, this project can be used as a template when product requires template restriction.",
        copy=False,
    )

    @api.constrains('sale_line_id')
    def _check_sale_line_type(self):
        for project in self.filtered(lambda project: project.sale_line_id):
            if project.sale_line_id.is_expense:
                raise ValidationError(_("You cannot link a billable project to a sales order item that comes from an expense or a vendor bill."))
