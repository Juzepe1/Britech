{
    'name': 'Documents - Sale Order',
    'summary': 'Sale Orders from Documents',
    'version': '18.0.0.0.2',
    'author': 'Ing. Josef Dostál',
    'license': 'Other proprietary',
    'depends': ['documents', 'documents_spreadsheet', 'sale'],
    'data': [
        'security/ir.model.access.csv', 
        'views/sale_order_views.xml', 'data/documents_folder_data.xml', 'data/ir_actions_server_data.xml', 'data/res_company_data.xml', 'views/res_config_settings_views.xml', 'views/documents_document_views.xml'],
    'installable': True,
    'application': False
}
