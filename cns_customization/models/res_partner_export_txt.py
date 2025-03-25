
from odoo import models
from odoo.http import request
import base64

class ResPartnerExport(models.TransientModel):
    _name = 'res.partner.export.txt'
    _description = 'Export Partnerů do TXT'

    def _get_initials(self, name):
        if not name:
            return ''
        name = name.strip()
        return name[0] + name[-1] if len(name) > 1 else name

    def export_selected_partners(self):
        partners = self.env['res.partner'].browse(self.env.context.get('active_ids', []))
        lines = []
        for p in partners:
            cislo = p.cns_cislo_clena_text or ''
            clen_2024 = "Ano" if getattr(p, 'clenem_v_2024', False) else "Ne"
            clen_2025 = "Ano" if getattr(p, 'clenem_v_2025', False) else "Ne"
            initials = self._get_initials(p.cns_name_striped or '')
            line = f"{cislo};2024;{clen_2024};2025;{clen_2025};Inicialy;{initials};"
            lines.append(line)

        content = "\n".join(lines)
        export = self.env['ir.attachment'].create({
            'name': 'export.txt',
            'type': 'binary',
            'datas': base64.b64encode(content.encode('utf-8')),
            'res_model': 'res.partner',
            'res_id': partners.ids[0] if partners else False,
            'mimetype': 'text/plain'
        })
        url = f'/web/content/{export.id}?download=true'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
