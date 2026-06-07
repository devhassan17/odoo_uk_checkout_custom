from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    mobile = fields.Char(string='Mobile')
