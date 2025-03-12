{
    'name': 'Product Technical Parameters Systee',
    'version': "18.0.1.0.0",
    'category': 'Product',
    'summary': 'Rozšíření product.category o volitelný typ součástky a úprava product.template (Systee)',
    'author': 'Vaše jméno / firma',
    'license': 'LGPL-3',
    'depends': ['product', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_category_views.xml',
        'views/product_template_views.xml',
        'views/product_template_search.xml',
        'data/product_technical_parameters_data.xml',
    ],
    'installable': True,
    'application': False,
}
