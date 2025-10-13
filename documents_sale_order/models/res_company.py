# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression

class ResCompany(models.Model):
    _inherit = "res.company"

    documents_sale_order_settings = fields.Boolean()
    sale_order_folder_id = fields.Many2one(
        'documents.document', string="Sale Order Workspace", check_company=True,
        compute='_compute_sale_order_folder_id', store=True, readonly=False,
        domain=[('type', '=', 'folder'), ('shortcut_document_id', '=', False)])
    sale_order_tag_ids = fields.Many2many('documents.tag', 'sale_order_tags_table')

    @api.depends('documents_sale_order_settings')
    def _compute_sale_order_folder_id(self):
        folder_id = self.env.ref('documents_sale_order.document_sale_order_folder', raise_if_not_found=False)
        self._reset_default_documents_folder_id('documents_sale_order_settings', 'sale_order_folder_id', folder_id)

    def _get_used_folder_ids_domain(self, folder_ids):
        return expression.OR([
            super()._get_used_folder_ids_domain(folder_ids),
            [('sale_order_folder_id', 'in', folder_ids), ('documents_sale_order_settings', '=', True)]
        ])