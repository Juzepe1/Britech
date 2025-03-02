# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

def pre_init_hook(cr):
    """Odstraní duplicity v ir.model.fields.selection před instalací modulu."""
    cr.execute("""
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model IN ('product.template', 'product.category')
        );
    """)
