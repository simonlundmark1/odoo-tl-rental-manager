{
    "name": "stock_rental_manager",
    "summary": "Rent out products during a specific date range",
    "version": "19.0.1.0.0",
    "author": "Simon Lundmark",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sales",

    "depends": [
        "base",
        "product",
        "sale",
    ],

    "data": [
        "security/ir.model.access.csv",
        "views/rental_order_views.xml",
    ],

    "application": True,
    "installable": True,
    "license": "LGPL-3",
}

