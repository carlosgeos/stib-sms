import os
import logging
import base64
import csv
from datetime import datetime
from collections import defaultdict
from flask import Flask, render_template
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

token = os.environ['ACCESS_TOKEN']
client_key = os.environ['CLIENT_KEY']
client_secret = os.environ['CLIENT_SECRET']

STIB_API_ADDR = "https://opendata-api.stib-mivb.be"


def setup_app():
    """Read all the stops information from the local GTFS file.

    stops_ids_by_name: Optimization, ID's are unique, names are
    not. When I look by name I want to know straight away the ID's
    linked to this stop name, instead of cycling though the list of
    stops each time

    Stop names are different for different types of transport. For
    example, Petillon stop has one for tram and one for metro.

    """
    # Dict containing all the info about the stops. Key is Stop ID
    stops_ids = {}

    stops_ids_by_name = defaultdict(list)  # Read docstring

    with open('data/stops.csv') as stopsfile:
        reader = csv.DictReader(stopsfile)
        stops_ids = {row['stop_id']: {
            'stop_name': row['stop_name'],
            'stop_lat': row['stop_lat'].strip(),
            'stop_lon': row['stop_lon'].strip(),
            'location_type': row['location_type']} for row in reader}

        for key, stop_dict in stops_ids.items():
            stops_ids_by_name[stop_dict['stop_name']].append(key)

    return stops_ids_by_name


stops = setup_app()


def get_token():
    """Gets a token from the token refresh endpoint
    """
    request_token_url = STIB_API_ADDR + '/token'
    # Base64 encode requires ASCII and we decode to utf8 afterwards
    # since the header must take a string and not ASCII byte literals
    base64_credentials = base64.b64encode((client_key + ":" + client_secret)
                                          .encode('ascii')).decode("utf-8")

    headers = {"Authorization": "Basic " + base64_credentials}
    data = "grant_type=client_credentials"

    r = requests.post(request_token_url, headers=headers, data=data)
    json_ob = r.json()

    token = json_ob['access_token']
    return token


def get_time(stop, token):

    ids = "%2C".join(stops[stop])  # %2C is a comma

    get_time_url = STIB_API_ADDR + '/OperationMonitoring/1.0/PassingTimeByPoint/' + ids

    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json"
    }

    r = requests.get(get_time_url, headers=headers)
    return r


@app.route('/')
def hello_world():
    token = get_token()
    stop = 'ULB'
    res = get_time(stop, token).json()

    for stops in res['points']:
        for vehicle in stops['passingTimes']:
            now = int(datetime.strftime(datetime.now(), "%-M"))
            expected = int(datetime.strftime(datetime.strptime(vehicle['expectedArrivalTime'], "%Y-%m-%dT%H:%M:%S"), "%-M"))

            vehicle['expectedArrivalTime'] = expected - now  # This is all broken. If time is 16:59 for example and expected is 17:01 it wont work.

    return render_template("main.html", stop=stop, payload=res)
