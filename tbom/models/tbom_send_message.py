# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TbomSendMessageWizard(models.TransientModel):
    _name = 'tbom.send.message.wizard'
    _description = 'TBOM Send Message Wizard'

    operation_id = fields.Many2one(
        'tbom.temporary.operation',
        string='Operation',
        required=True
    )
    recipient_email = fields.Char(
        string='Recipient Email',
        required=True
    )
    subject = fields.Char(
        string='Subject',
        required=True
    )
    body = fields.Text(
        string='Message',
        required=True
    )

    @api.constrains('recipient_email')
    def _check_email(self):
        for record in self:
            if record.recipient_email:
                email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                if not re.match(email_regex, record.recipient_email):
                    raise ValidationError("Please enter a valid email address.")

    def action_send_message(self):
        self.ensure_one()
        # Find if there's a configured outgoing mail server
        mail_server = self.env['ir.mail_server'].search([], limit=1)
        if not mail_server:
            raise ValidationError("No outgoing mail server (SMTP) is configured in Odoo. Please configure one in Settings -> Outgoing Mail Servers.")

        # Create the email using Odoo's native mail.mail model
        mail_values = {
            'subject': self.subject,
            'body_html': f"<p>{self.body.replace('\n', '<br/>')}</p>",
            'email_to': self.recipient_email,
            'email_from': mail_server.smtp_user or self.env.user.email or 'tbom@example.com',
            'res_id': self.operation_id.id,
            'model': 'tbom.temporary.operation',
        }
        
        try:
            # Create and send the mail record
            mail = self.env['mail.mail'].create(mail_values)
            if mail:
                # Send the email immediately
                mail.send(raise_exception=True)
        except Exception as e:
            raise ValidationError(f"Failed to send email through the mail server: {str(e)}")
        
        # Log the message in the chatter as well
        self.operation_id.message_post(
            body=f"<b>Sent Message to {self.recipient_email}:</b><br/>{self.body.replace('\n', '<br/>')}",
            subject=self.subject,
            subtype_xmlid='mail.mt_comment'
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Message sent successfully to the recipient!',
                'type': 'success',
                'sticky': False,
            }
        }
