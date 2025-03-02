# -*- coding: utf-8 -*-

def post_init_hook(cr, registry):
    """Odstraní duplicity v ir.model.fields.selection po instalaci modulu."""
    cr.execute("""
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model IN ('product.template', 'product.category')
        );
    """)
