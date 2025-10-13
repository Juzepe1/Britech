# -*- coding: utf-8 -*-
# Version tag for debugging in logs:
# documents_sale_order.document_xlsx_link VERSION = 1.0.3 (no attachment writes)
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)

class Document(models.Model):
    _inherit = 'documents.document'

    def clone_xlsx_into_spreadsheet(self, archive_source=False):
        self.ensure_one()
        new_id = super(Document, self).clone_xlsx_into_spreadsheet(archive_source=archive_source)
        new_doc = self.browse(new_id)

        # Decide link: prefer sale.order (your computed), fallback to res_model/res_id
        res_model = False
        res_id = False
        sale_order = getattr(self, 'sale_order_id', False)
        if sale_order:
            res_model, res_id = 'sale.order', sale_order.id
        elif self.res_model and self.res_id:
            res_model, res_id = self.res_model, self.res_id

        vals = {}
        for fname in ('folder_id', 'owner_id', 'partner_id'):
            if self[fname]:
                vals[fname] = self[fname].id
        if res_model and res_id:
            vals.update({'res_model': res_model, 'res_id': res_id})

        if vals:
            _logger.info("documents_sale_order v1.0.3: set meta on new doc %s: %s", new_doc.id, vals)
            new_doc.sudo().write(vals)
        # Do not touch spreadsheet model links; only set on documents.document.
        return new_id
