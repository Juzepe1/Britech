# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    documents_sale_order_settings = fields.Boolean(related='company_id.documents_sale_order_settings', readonly=False)
    sale_order_folder_id = fields.Many2one(related='company_id.sale_order_folder_id', readonly=False)
    sale_order_tag_ids = fields.Many2many(related='company_id.sale_order_tag_ids', readonly=False)