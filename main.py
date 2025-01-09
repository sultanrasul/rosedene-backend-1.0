import requests
from datetime import datetime
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from flask import Flask, request, jsonify

import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


# Apartment IDs dictionary
apartment_ids = {
    3069140: 'Emperor Apartment 1',
    3070529: 'Emperor Apartment 2',
    3070534: 'Emperor Apartment 6',
    3070536: 'Emperor Apartment 7',
    3070531: 'King Studio Apartment 4',
    3070533: 'King Studio Apartment 5',
    3070540: 'King Studio Apartment 9',
    3070538: 'The Cottage Apartment 10',
    3070537: 'The Cottage Apartment 8',
    3070530: 'Emperor Studio Apartment 3',

}

# API credentials and endpoints
username = os.getenv('username')
password = os.getenv('password')
api_endpoint = "https://new.rentalsunited.com/api/handler.ashx"


# Define a route to handle chat messages
@app.route('/blocked_apartments', methods=['POST'])
def check_blocked_apartments():
    # Check Blocked Apartments
    
    date_from = request.json['date_from']
    date_to = request.json['date_to']

    print(date_from,date_to)
    
    props_request = Pull_ListPropertiesBlocks_RQ(
        username, password, location_id=7912,
        date_from=datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"]), 
        date_to=datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    )
    
    response = requests.post(api_endpoint, data=props_request.serialize_request(), headers={"Content-Type": "application/xml"})
    properties = props_request.check_blocked_properties(response.text, apartment_ids)

    return jsonify({'properties': properties})



@app.route('/check_calendar', methods=['POST'])
def check_calendar():

    date_from = request.json['date_from']
    date_to = request.json['date_to']
    property_id = request.json['property_id']

    print(date_from,date_to,property_id)
    

    # Check Availability Calendar
    avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
        username, password, property_id=property_id,
        date_from=datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"]), 
        date_to=datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    )

    response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})
    calendar = avail_request.check_availability_calendar(response.text)

    return calendar

if __name__ == '__main__':
    app.run()