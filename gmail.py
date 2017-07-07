import gnupg
import os
import httplib2
import base64

from email.mime.text import MIMEText
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


class GmailService:
    tmpdir = os.environ['TMPDIR']
    default_num = os.environ['GSM_NUM']
    default_email_addr = os.environ['EMAIL_ADDR']
    passphrase = os.environ['GPG_PASSPHRASE']  # File encryption
    ENCRYPTED_FILE = "encrypted.ejson"
    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/gmail-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/gmail.compose'
    CLIENT_SECRET_FILE = tmpdir + 'client_secrets.json'  # TODO: Check if file is there or call decrypt_and_write_file()
    APPLICATION_NAME = 'STIB SMS Waiting times'

    def __init__(self):
        """Prepares the credentials and saves the service.
        """
        self.decrypt_and_write_file()
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)

    def decrypt_and_write_file(self):
        """Reads an encrypted file in the filesystem (also on GitHub !),
        decrypts it using an environment variable and writes the result to
        the TMPDIR of the actual machine.

        """
        gpg = gnupg.GPG()
        with open(GmailService.ENCRYPTED_FILE, "rb") as client_secrets:
            gpg.decrypt_file(client_secrets,
                             passphrase=GmailService.passphrase,
                             output=GmailService.tmpdir + "client_secrets.json")

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
        Credentials, the obtained credential.
        """
        credential_path = os.path.join(GmailService.tmpdir, 'credentials.json')
        # Touch the file
        with open(credential_path, 'a'):
            os.utime(credential_path, None)

            store = Storage(credential_path)
            credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(GmailService.CLIENT_SECRET_FILE,
                                                  GmailService.SCOPES)
            flow.user_agent = GmailService.APPLICATION_NAME
            credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def create_message(self, sender=default_email_addr, to=default_num,
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

    def send_message(self, user_id, message):
        """Send an email message.

        Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent. In base64url

        Returns:
        Sent Message.
        """
        message = (self.service.users().messages().send(userId=user_id,
                                                        body=message).execute())

        return message
