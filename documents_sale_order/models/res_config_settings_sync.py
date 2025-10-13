# -*- coding: utf-8 -*-
from odoo import models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def action_open_documents_so_sync(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Link Sale Order Attachments into Documents',
            'res_model': 'documents.sale.order.sync.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_only_missing_documents': True},
        }
