# File: odoo_uk_checkout_custom/models/res_company.py
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    x_checkout_country_ids = fields.Many2many(
        "res.country",
        string="Allowed Checkout Countries",
        help="Restricts checkout to only these countries for this company. Leave empty for all countries.",
    )
    
    helpdesk_force_team_email = fields.Boolean(
        string="Force Team Email in Helpdesk",
        help="When sending messages from helpdesk tickets, override the From address with the Team Alias.",
        default=False,
    )



class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    x_checkout_country_ids = fields.Many2many(
        related="company_id.x_checkout_country_ids",
        readonly=False,
        string="Allowed Checkout Countries",
        help="Restricts checkout to only these countries for this company. Leave empty for all countries.",
    )

    helpdesk_force_team_email = fields.Boolean(
        related="company_id.helpdesk_force_team_email",
        readonly=False,
    )


