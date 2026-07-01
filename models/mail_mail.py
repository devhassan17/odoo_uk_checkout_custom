# -*- coding: utf-8 -*-

from odoo import models, api
from email.utils import formataddr

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('model') == 'helpdesk.ticket' and vals.get('res_id'):
                ticket = self.env['helpdesk.ticket'].browse(vals['res_id'])
                if ticket.exists():
                    company = ticket.company_id or self.env.company
                    if company.helpdesk_force_team_email and ticket.team_id and ticket.team_id.alias_email:
                        # 1. Format the team email dynamically
                        alias_email = ticket.team_id.alias_email
                        team_name = ticket.team_id.name
                        formatted_email = formataddr((team_name, alias_email))
                        
                        # 2. Force both From and Reply-To addresses
                        vals['email_from'] = formatted_email
                        vals['reply_to'] = formatted_email
                        
                        # 3. Find the matching Titan Outgoing Mail Server
                        titan_server = self.env['ir.mail_server'].sudo().search([
                            ('smtp_user', '=', alias_email)
                        ], limit=1)
                        
                        # 4. Force the email to route strictly through this server
                        if titan_server:
                            vals['mail_server_id'] = titan_server.id

        return super(MailMail, self).create(vals_list)
