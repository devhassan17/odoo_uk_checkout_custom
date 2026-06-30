# -*- coding: utf-8 -*-

from odoo import models, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def message_post(self, **kwargs):
        if self.env.company.helpdesk_force_team_email:
            # We don't want to override internal notes
            if kwargs.get('subtype_xmlid') != 'mail.mt_note' and kwargs.get('message_type') in ('comment', 'email'):
                if self.team_id and self.team_id.alias_email:
                    # team_id.alias_email is usually something like 'alias@domain.com'
                    # team_id.name is the name of the team
                    # Format nicely as "Team Name" <alias@domain.com>
                    # Actually we can use the formataddr from email.utils
                    from email.utils import formataddr
                    
                    # Alternatively just do string formatting
                    alias_name_email = self.team_id.alias_email
                    team_name = self.team_id.name
                    formatted_email = formataddr((team_name, alias_name_email))
                    
                    kwargs['email_from'] = formatted_email

        return super(HelpdeskTicket, self).message_post(**kwargs)
