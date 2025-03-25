
from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    from odoo.api import Environment
    env = api.Environment(cr, SUPERUSER_ID, {})
    partners = env['res.partner'].search([])
    for partner in partners:
        partner.write({'cns_name_striped': partner._remove_titles(partner.name)})
