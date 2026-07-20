import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_first_name = fields.Char(string='First Name', compute='_compute_split_name', inverse='_inverse_split_name', store=True)
    x_last_name = fields.Char(string='Last Name', compute='_compute_split_name', inverse='_inverse_split_name', store=True)
    x_marketing_opt_in = fields.Boolean(string='Marketing Opt-in')

    @api.depends('name')
    def _compute_split_name(self):
        for partner in self:
            try:
                first_name = ''
                last_name = ''
                if partner.name:
                    parts = partner.name.strip().split()
                    if parts:
                        first_name = parts[0]
                        last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                partner.x_first_name = first_name
                partner.x_last_name = last_name
            except Exception as e:
                _logger.exception("Error computing split name for partner %s: %s", getattr(partner, 'id', None), e)
                partner.x_first_name = False
                partner.x_last_name = False

    def _inverse_split_name(self):
        for partner in self:
            try:
                full_name = ' '.join(p for p in [partner.x_first_name, partner.x_last_name] if p).strip()
                if full_name:
                    partner.name = full_name
            except Exception as e:
                _logger.exception("Error setting inverse split name for partner %s: %s", getattr(partner, 'id', None), e)
