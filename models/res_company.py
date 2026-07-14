# File: odoo_uk_checkout_custom/models/res_company.py
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    x_checkout_country_ids = fields.Many2many(
        "res.country",
        string="Allowed Checkout Countries",
        help="Restricts checkout to only these countries for this company. Leave empty for all countries.",
    )
    x_enable_custom_billing_address = fields.Boolean(
        string="Enable Custom Billing Address on Checkout",
        default=False,
        help="If checked, enables the custom billing address option on the storefront for this company. Otherwise, uses default Odoo checkout billing logic.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    x_checkout_country_ids = fields.Many2many(
        related="company_id.x_checkout_country_ids",
        readonly=False,
        string="Allowed Checkout Countries",
        help="Restricts checkout to only these countries for this company. Leave empty for all countries.",
    )
    x_enable_custom_billing_address = fields.Boolean(
        related="company_id.x_enable_custom_billing_address",
        readonly=False,
        string="Enable Custom Billing Address on Checkout",
        help="If checked, enables the custom billing address option on the storefront for this company. Otherwise, uses default Odoo checkout billing logic.",
    )


