# -*- coding: utf-8 -*-

from odoo import models, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def message_post(self, **kwargs):
        if self.env.company.helpdesk_force_team_email:
            # We don't want to override internal notes
            if kwargs.get('subtype_xmlid') != 'mail.mt_note' and kwargs.get('message_type') in ('comment', 'email'):
                reply_to = kwargs.get('reply_to')
                if not reply_to:
                    # Odoo dynamically generates the reply_to for records, let's pull it
                    reply_to = self._notify_get_reply_to(default=None)[self.id]
                
                if reply_to:
                    kwargs['email_from'] = reply_to

        return super(HelpdeskTicket, self).message_post(**kwargs)
