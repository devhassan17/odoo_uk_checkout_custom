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
                if ticket.exists():
                    reply_to = ticket._notify_get_reply_to(default=None)[ticket.id]
                    if reply_to:
                        res['email_from'] = reply_to

        return res
