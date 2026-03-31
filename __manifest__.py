{
    'name': 'UK Checkout Customisations',
    'version': '19.0.1.1.0',
    'summary': 'Custom checkout changes for UK D2C stores',
    'description': """
Adds custom-only checkout features for UK D2C stores:
- First Name / Last Name checkout inputs
- Hidden full Name sync for standard Odoo checkout
- Optional UK phone validation on checkout
- Postcode label + UK postcode validation
- Remove Company / VAT / State fields from checkout UI
- Marketing opt-in checkbox saved on customer/contact

Not included because they are better handled by settings or third-party apps:
- Restrict shipping to UK only (configure delivery methods)
- One-page / one-step checkout
""",
    'author': 'Managemyweb.co',
    'license': 'LGPL-3',
    'category': 'Website/eCommerce',
    'depends': ['website_sale', 'contacts', 'mail'],
    'data': [
        'views/res_partner_views.xml',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_uk_checkout_custom/static/src/css/checkout_custom.css',
            'odoo_uk_checkout_custom/static/src/js/checkout_custom.js',
        ],
    },
    'installable': True,
    'application': False,
}
