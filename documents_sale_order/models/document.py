# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Document(models.Model):
    _inherit = 'documents.document'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order",
                                    compute='_compute_sale_order', store=False,
                                    search='_search_sale_order_id')

    @api.depends('res_id', 'res_model')
    def _compute_sale_order(self):
        SaleOrder = self.env['sale.order']
        for document in self:
            document.sale_order_id = document.res_model == 'sale.order' and SaleOrder.browse(document.res_id) or False

    def _search_sale_order_id(self, operator, value):
        # Enable searching on sale_order_id in Documents (maps to res_model/res_id)
        if operator not in ('=', '!='):
            # Fallback to default behavior for unsupported operators
            return [('id', operator, value)]
        if not value:
            # search for empty
            return [('res_model', '!=', 'sale.order')] if operator == '=' else [('res_model', '=', 'sale.order')]
        return [('res_model', '=', 'sale.order'), ('res_id', operator, value.id if hasattr(value, 'id') else value)]

    # Optional: simple helper to create a sale order from a document (called by server action)
    def action_create_sale_order(self):
        self.ensure_one()
        partner = self.partner_id or self.env.user.company_id.partner_id
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'origin': _('Created from Document %s') % (self.display_name or self.name),
        })
        # Link the document to the created SO
        self.write({'res_model': 'sale.order', 'res_id': order.id})
        view_id = order.get_formview_id()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'name': _('New Sale Order'),
            'context': self.env.context,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': order.id,
            'view_id': view_id,
        }