# File: odoo_uk_checkout_custom/models/res_company.py
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    x_checkout_country_ids = fields.Many2many(
        "res.country",
        string="Allowed Checkout Countries",
        help="Restricts checkout to only these countries for this company. Leave empty for all countries.",
    )



