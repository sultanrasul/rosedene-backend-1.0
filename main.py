import requests
from datetime import datetime
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from flask import Flask, request, jsonify

import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)



discordUrl = os.getenv("DISCORD-URL")

orbitTechIcon = "https://cdn.discordapp.com/attachments/743206830209237103/1114538805203058738/funkypanda.png?ex=6533cb26&is=65215626&hm=6483ee595d1b4a9f59264947f09fe1da2d1f91a2b19f4eb98d56c9e5f7970d24&"

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


# Apartment IDs dictionary
apartment_ids = {
    3069140: 'Rosedene Highland House - Emperor Apartment 1',
    3070529: 'Rosedene Highland House - Emperor Apartment 2',
    3070534: 'Rosedene Highland House - Emperor Apartment 6',
    3070536: 'Rosedene Highland House - Emperor Apartment 7',
    3070531: 'Rosedene Highland House - King Studio Apartment 4',
    3070533: 'Rosedene Highland House - King Studio Apartment 5',
    3070540: 'Rosedene Highland House - King Studio Apartment 9',
    3070538: 'Rosedene Highland House - The Cottage Apartment 10',
    3070537: 'Rosedene Highland House - The Cottage Apartment 8',
    3070530: 'Rosedene Highland House - Emperor Studio Apart 3',

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