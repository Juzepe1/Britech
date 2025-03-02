{
    'name': 'Product Technical Properties',
    'version': '1.0',
    'category': 'Product',
    'summary': 'Adds technical properties fields to products',
    'depends': ['product'],
    'data': [
        'views/product_template_view.xml',
        'views/product_category_view.xml',
    ],
    'installable': True,
    'application': False,
    'pre_init_hook': 'pre_init_hook.pre_init_hook',
}
