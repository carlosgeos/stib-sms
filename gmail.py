import gnupg
import os
import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from gmail_message import create_message, send_message

tmpdir = os.environ['TMPDIR']
passphrase = os.environ['GPG_PASSPHRASE']  # File encryption
ENCRYPTED_FILE = "encrypted.ejson"


def decrypt_and_write_file():
    """Reads an encrypted file in the filesystem (also on GitHub !),
    decrypts it using an environment variable and writes the result to
    the TMPDIR of the actual machine.

    """
    gpg = gnupg.GPG()
    with open(ENCRYPTED_FILE, "rb") as client_secrets:
        gpg.decrypt_file(client_secrets, passphrase=passphrase,
                         output=tmpdir + "client_secrets.json")


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.compose'
CLIENT_SECRET_FILE = tmpdir + 'client_secrets.json'  # TODO: Check if file is there or call decrypt_and_write_file()
APPLICATION_NAME = 'STIB SMS Waiting times'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_path = os.path.join(tmpdir, 'credentials.json')
    # Touch the file
    with open(credential_path, 'a'):
        os.utime(credential_path, None)

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials



def main():
    """
    """
    decrypt_and_write_file()
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    message = create_message()
    send_message(service, user_id="me", message=message)

main()
