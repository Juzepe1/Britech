# -*- coding: utf-8 -*-

def pre_init_hook(cr_or_env):
    """Kompletně odstraní konfliktní výběrové hodnoty v ir.model.fields a ir.model.fields.selection."""

    # Detekce, zda byl hook zavolán s `cr` nebo `env`, a získání `cr`
    if hasattr(cr_or_env, 'cr'):  # Pokud je `cr_or_env` environment, získáme `cr`
        cr = cr_or_env.cr
    else:
        cr = cr_or_env  # Pokud je to přímo `cr`, použijeme ho

    cr.execute("""
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model IN ('product.template', 'product.category')
        );
    """)
    
    cr.execute("""
        DELETE FROM ir_model_fields 
        WHERE model IN ('product.template', 'product.category')
        AND name IN (
            'ptp_cap_unit', 'ptp_cap_dielectric', 'ptp_cap_footprint', 
            'ptp_res_unit', 'ptp_res_footprint', 'ptp_component_type'
        );
    """)
