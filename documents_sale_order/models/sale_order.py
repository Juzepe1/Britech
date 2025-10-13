# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'documents.mixin']

    document_count = fields.Integer(string='Documents', compute='_compute_document_count', store=False)

    def _compute_document_count(self):
        if not self.ids:
            for rec in self:
                rec.document_count = 0
            return
        groups = self.env['documents.document'].read_group(
            [('res_model', '=', 'sale.order'), ('res_id', 'in', self.ids)],
            ['res_id'],
            ['res_id']
        )
        count_map = {}
        for g in groups:
            key = g.get('res_id')
            if isinstance(key, tuple):
                key = key[0]
            count = g.get('res_id_count') or g.get('__count') or 0
            count_map[key] = count
        for order in self:
            order.document_count = count_map.get(order.id, 0)

    def action_view_documents(self):
        self.ensure_one()
        action = self.env.ref('documents.document_action').sudo().read()[0]
        action['domain'] = [('res_model', '=', 'sale.order'), ('res_id', '=', self.id)]
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_res_model': 'sale.order',
            'default_res_id': self.id,
            'default_partner_id': self.partner_id.id,  # prefill partner from SO
        })
        # Provide a sensible default folder if configured at company level
        company = self.company_id or self.env.company
        if getattr(company, 'sale_order_folder_id', False):
            ctx['default_folder_id'] = company.sale_order_folder_id.id
        action['context'] = ctx
        return action

    # documents.mixin hooks (kept from earlier module so behavior stays consistent)
    def _get_document_vals_access_rights(self):
        return {'access_internal': 'view', 'access_via_link': 'view'}

    def _get_document_owner(self):
        return self.env.user

    def _get_document_tags(self):
        company = self.company_id or self.env.company
        return company.sale_order_tag_ids

    def _get_document_folder(self):
        company = self.company_id or self.env.company
        return company.sale_order_folder_id

    def _check_create_documents(self):
        company = self.company_id or self.env.company
        return company.documents_sale_order_settings and super()._check_create_documents()


    # Alias to match smart button name used in the view
    def action_open_documents(self):
        # keep a single implementation path
        return self.action_view_documents()
