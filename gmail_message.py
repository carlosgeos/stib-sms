import os
import base64
from email.mime.text import MIMEText

default_num = os.environ['GSM_NUM']
default_email_addr = os.environ['EMAIL_ADDR']


def create_message(sender=default_email_addr, to=default_num,
                   subject="STIB waiting times",
                   message_text="Patience please !"):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to + "@sms.easymessaging.orange.be"
    message['from'] = sender
    message['subject'] = subject
    # I found the following (JSON, base64url, ascii) line down below to
    # work with Python 3 and the GMail send API.
    return {'raw': base64.urlsafe_b64encode(bytes(message)).decode("ascii")}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent. In base64url

    Returns:
    Sent Message.
    """
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())

    return message
