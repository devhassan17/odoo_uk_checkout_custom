# -*- coding: utf-8 -*-

from odoo import models, api, tools

class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None,
                   smtp_debug=False, smtp_session=None):
        
        # If no explicit mail_server_id or smtp_server is provided, Odoo is about to search for a fallback server.
        # We intercept this to force Odoo to use the underlying Odoo.sh configuration (if available), 
        # completely bypassing the custom Titan servers for non-Helpdesk emails.
        if not mail_server_id and not smtp_server:
            # Check if odoo.sh config actually has an smtp_server defined
            config_smtp = tools.config.get('smtp_server')
            
            if config_smtp:
                smtp_server = config_smtp
                smtp_port = tools.config.get('smtp_port', 25)
                smtp_user = tools.config.get('smtp_user', False)
                smtp_password = tools.config.get('smtp_password', False)
                smtp_encryption = 'ssl' if tools.config.get('smtp_ssl') else False
            else:
                # If running locally or no config provided, force localhost to mimic default Odoo behavior
                smtp_server = 'localhost'
                smtp_port = 25
                smtp_user = False
                smtp_password = False
                smtp_encryption = False
                
        return super(IrMailServer, self).send_email(
            message, mail_server_id=mail_server_id, smtp_server=smtp_server, 
            smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password, 
            smtp_encryption=smtp_encryption, smtp_debug=smtp_debug, smtp_session=smtp_session
        )
