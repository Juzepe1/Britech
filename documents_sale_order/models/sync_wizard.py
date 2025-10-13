# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class DocumentsSaleOrderSyncWizard(models.TransientModel):
    _name = 'documents.sale.order.sync.wizard'
    _description = 'Link all Sale Order attachments into Documents'

    limit = fields.Integer(
        string="Max items (0 = no limit)",
        default=0,
        help="Limit how many attachments to process in this run. Use 0 to process all."
    )
    only_missing_documents = fields.Boolean(
        string="Only missing Documents",
        default=True,
        help="If enabled, only attachments without a corresponding Documents record will be created. "
             "If disabled, existing Documents will be updated with the proper link and metadata."
    )

    def action_run(self):
        self.ensure_one()
        env = self.env
        Doc = env['documents.document'].sudo()
        Att = env['ir.attachment'].sudo()
        Sale = env['sale.order'].sudo()

        domain = [
            ('res_model', '=', 'sale.order'),
            ('res_id', '!=', False),
            ('type', '=', 'binary'),
        ]
        atts = Att.search(domain, limit=self.limit or None)

        created, updated = 0, 0
        for att in atts:
            order = Sale.browse(att.res_id)
            doc = Doc.search([('attachment_id', '=', att.id)], limit=1)

            # Find a folder from any existing SO document (if present)
            folder_id = False
            if order.exists():
                so_doc_with_folder = Doc.search([
                    ('res_model', '=', 'sale.order'),
                    ('res_id', '=', order.id),
                    ('folder_id', '!=', False)
                ], limit=1)
                if so_doc_with_folder:
                    folder_id = so_doc_with_folder.folder_id.id

            vals_common = {
                'res_model': 'sale.order',
                'res_id': order.id if order.exists() else att.res_id,
            }
            if folder_id:
                vals_common['folder_id'] = folder_id
            if order.exists() and order.partner_id:
                vals_common['partner_id'] = order.partner_id.id

            if doc:
                if not self.only_missing_documents:
                    doc.write(vals_common)
                    updated += 1
            else:
                Doc.create({
                    'name': att.name or att.datas_fname or 'Attachment',
                    'type': 'binary',
                    'attachment_id': att.id,
                    **vals_common
                })
                created += 1

        message = _("Sync done: %s created, %s updated") % (created, updated)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _("Documents Sync"), 'message': message, 'sticky': False},
        }
