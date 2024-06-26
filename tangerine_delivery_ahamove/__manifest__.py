# -*- coding: utf-8 -*-
{
    'name': 'Ahamove Shipping',
    'summary': """Ahamove shipping module will allow shippers to easily place, cancel, get quotes, and track orders via simple integration for delivery in Odoo.""",
    'author': 'Long Duong Nhat',
    'category': 'Inventory/Delivery',
    'support': 'odoo.tangerine@gmail.com',
    'version': '17.0.1.0',
    'depends': ['tangerine_delivery_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/delivery_ahamove_data.xml',
        'data/ahamove_route_api_data.xml',
        'data/ahamove_status_data.xml',
        'data/res_partner_data.xml',
        'data/res_country_state_data.xml',
        'wizard/choose_delivery_carrier_wizard_views.xml',
        'views/delivery_ahamove_views.xml',
        'views/ahamove_res_state_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
        'views/ahamove_service_views.xml',
        'views/ahamove_service_request_views.xml',
    ],
    'images': ['static/description/thumbnail.png'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': True,
    'currency': 'USD',
    'price': 128.00
}