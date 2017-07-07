import os
import base64
import csv
from datetime import datetime
from collections import defaultdict
import requests

class StibService:
    token = os.environ['ACCESS_TOKEN']
    client_key = os.environ['CLIENT_KEY']
    client_secret = os.environ['CLIENT_SECRET']

    STIB_API_ADDR = "https://opendata-api.stib-mivb.be"

    def __init__(self):
        "docstring"
        self.stops_by_name, self.stops_by_ids = self.setup_service()
        self.token = self.get_token()
        self.headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json"
        }

    def setup_service(self):
        """Read all the stops information from the local GTFS file.

        stops_ids_by_name: ID's are unique, names are not. Therefore
        when I look by name I want to know straight away the ID's
        linked to this stop name, instead of cycling though the list
        of stops each time.

        Stop names are different for different types of transport. For
        example, Petillon stop has one for tram and one for metro. One
        name, two or more ids.

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

        return stops_ids_by_name, stops_ids

    def get_token(self):
        """Gets a token from the token refresh endpoint. The type of
        authorization required to make an API call is to include the
        header: 'Authorization: Basic base64(<clientkey:clientsecret>)'

        """
        request_token_url = StibService.STIB_API_ADDR + '/token'
        # Base64 encode requires ASCII and we decode to utf8 afterwards
        # since the header must take a string and not ASCII byte literals
        base64_credentials = base64.b64encode((StibService.client_key + ":" +
                                               StibService.client_secret)
                                              .encode('ascii')).decode("utf-8")

        # these are different headers to get the token !!
        headers = {"Authorization": "Basic " + base64_credentials}
        data = "grant_type=client_credentials"

        r = requests.post(request_token_url, headers=headers, data=data)
        json_ob = r.json()

        token = json_ob['access_token']

        return token

    def get_time(self, stop):
        """Looks up the arrival time of all vehicles arriving at the stop (can
        be in any direction and there might be several physical stops
        with the same time). These are looked up too.

        Returns: the response from the API, with a flawed modification. TODO

        """
        self.token = self.get_token()      # Refresh token
        ids = "%2C".join(self.stops_by_name[stop])  # %2C is a comma

        get_time_url = StibService.STIB_API_ADDR + \
                       '/OperationMonitoring/1.0/PassingTimeByPoint/' + \
                       ids

        r = requests.get(get_time_url, headers=self.headers).json()

        if r['points'] is not None:         # No vehicles, might be 3am...
            for stops in r['points']:
                for vehicle in stops['passingTimes']:
                    now = int(datetime.strftime(datetime.now(), "%-M"))
                    expected = int(datetime.strftime(datetime.strptime(vehicle['expectedArrivalTime'], "%Y-%m-%dT%H:%M:%S"), "%-M")) # Keep only minutes -> FAIL

                    # This is all broken. If time is 16:59 for example and
                    # expected is 17:01 it wont work.
                    vehicle['expectedArrivalTime'] = expected - now

        return r

    def get_line(self, *line_numbers):
        """Checks the position of all vehicles on these line_numbers.

        Returns: their direction and the stop where they're at.

        """
        self.token = self.get_token()      # Refresh token
        line_numbers = "%2C".join(str(n) for n in line_numbers)  # %2C is a comma
        get_line_url = StibService.STIB_API_ADDR + \
                       '/OperationMonitoring/1.0/VehiclePositionByLine/' + \
                       line_numbers

        r = requests.get(get_line_url, headers=self.headers).json()
        texto = ""              # Text message to send
        for line in r['lines']:
            texto += "Line " + str(line['lineId']) + ":\n"
            # I need the following structure to efficiently parse the
            # vehicles
            vehicles_by_direction = defaultdict(list)
            for vehicle in line['vehiclePositions']:
                vehicles_by_direction[vehicle['directionId']].append(
                    # Store a tuple: the stop these vehicles last
                    # crossed and the distance in meters from it
                    (vehicle['pointId'], vehicle['distanceFromPoint'])
                )
            # Now the text message can be easily built
            for direction, vehicles in vehicles_by_direction.items():
                try:
                    try:
                        direction_stop_name = self.stops_by_ids[str(direction)]['stop_name']
                    except KeyError:
                        # Stop name has an 'F' sometimes for some reason...
                        direction_stop_name = self.stops_by_ids[str(direction) + 'F']['stop_name']
                except:
                    direction_stop_name = "NaN"
                texto += direction_stop_name + "\n"
                for vehicle in vehicles:
                    # id_to_look_for -> padded string to match stops.txt
                    id_to_look_for = str(vehicle[0]).zfill(4)
                    try:
                        try:
                            current_stop_name = self.stops_by_ids[id_to_look_for]['stop_name']
                        except KeyError:
                            current_stop_name = self.stops_ids_by_name[id_to_look_for + 'F']['stop_name']
                    except:
                        current_stop_name = "NaN"

                    distance_from_current_stop = str(vehicle[1])
                    texto += current_stop_name.lower() + "\n"
                    # distance_from_current_stop + " m\n"

        return texto
