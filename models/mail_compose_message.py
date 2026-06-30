# -*- coding: utf-8 -*-

from odoo import models, api
from email.utils import formataddr

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.model
    def default_get(self, fields_list):
        res = super(MailComposeMessage, self).default_get(fields_list)
        
        # Check if we are composing for a helpdesk ticket
        if self.env.context.get('active_model') == 'helpdesk.ticket' and self.env.context.get('active_ids'):
            if self.env.company.helpdesk_force_team_email:
                ticket_id = self.env.context.get('active_ids')[0]
                ticket = self.env['helpdesk.ticket'].browse(ticket_id)
                if ticket.exists() and ticket.team_id and ticket.team_id.alias_email:
                    # Update email_from
                    alias_name_email = ticket.team_id.alias_email
                    team_name = ticket.team_id.name
                    formatted_email = formataddr((team_name, alias_name_email))
                    
                    res['email_from'] = formatted_email
                    
        return res
