# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Doc = env['documents.document']
    Att = env['ir.attachment']
    Sale = env['sale.order']

    # All binary attachments already linked to sale.order
    attachments = Att.search([
        ('res_model', '=', 'sale.order'),
        ('res_id', '!=', False),
        ('type', '=', 'binary')
    ])

    for att in attachments:
        # Skip attachments that are already represented by a document
        doc = Doc.search([('attachment_id', '=', att.id)], limit=1)
        order = Sale.browse(att.res_id)

        # Try to reuse a folder from any existing SO document (if one exists)
        folder_id = False
        so_doc_with_folder = Doc.search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', order.id),
            ('folder_id', '!=', False)
        ], limit=1)
        if so_doc_with_folder:
            folder_id = so_doc_with_folder.folder_id.id

        vals = {
            'name': att.name or att.datas_fname or 'Attachment',
            'type': 'binary',
            'attachment_id': att.id,
            'res_model': 'sale.order',
            'res_id': order.id,
        }
        # Soft metadata (optional)
        if folder_id:
            vals['folder_id'] = folder_id
        if order.partner_id:
            vals['partner_id'] = order.partner_id.id

        if doc:
            # Ensure correct link & metadata on existing document
            update = {'res_model': 'sale.order', 'res_id': order.id}
            if folder_id and (not doc.folder_id or doc.folder_id.id != folder_id):
                update['folder_id'] = folder_id
            if order.partner_id and (not doc.partner_id or doc.partner_id.id != order.partner_id.id):
                update['partner_id'] = order.partner_id.id
            if update:
                doc.sudo().write(update)
        else:
            # Create a new document for this attachment
            Doc.sudo().create(vals)
