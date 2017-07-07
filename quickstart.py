import logging
# from datetime import datetime
from flask import Flask, render_template, request, jsonify

from gmail import GmailService
from stib import StibService

app = Flask(__name__)
stib_service = StibService()
gmail_service = GmailService()
logging.basicConfig(level=logging.DEBUG)


@app.route('/')
def web_interface():
    """Quick and dirty web interface with a GET parameter. Not really the
    purpose of the project. Mainly there to accept Gmail's OAuth2.

    """
    stop = request.args.get('stop')
    if stop:
        stop = stop.upper()
        res = stib_service.get_time(stop)
    else:
        stop = "No stop provided in GET arguments"
        res = []

    return render_template('main.html', stop=stop, payload=res)


@app.route('/stib', methods=['POST'])
def check_times():
    """A POST request to '/stib' is sent by Twilio with a lot of
    info. Here, the info is parsed

    There is no response to Twilio since it doesn't have to do
    anything else other than receiving messages and sending an HTTP
    request to '/stib'.

    If the SMS response was sent by Twilio (it is more expensive), a
    response in TwiML format would have to be given

    """
    sms_content = {
        'from': request.form['From'],
        'to': request.form['to'],
        'sms_body': request.form['Body'],
        'num_media': request.form['NumMedia'],
        'message_sid': request.form['MessageSid'],
        'account_sid': request.form['AccountSid'],
        'service_sid': request.form['MessagingServiceSid'],
    }                           # Twilio request POST content

    line_numbers = sms_content['sms_body'].split(' ')
    network_info = stib_service.get_line(*line_numbers)

    message = gmail_service.create_message(message_text=network_info)
    gmail_service.send_message(user_id="me", message=message)

    return jsonify(
        status="OK"
    )
