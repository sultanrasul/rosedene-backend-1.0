import requests
from datetime import datetime
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from property_price import Pull_ListPropertyPrices_RQ
from flask import Flask, request, jsonify, redirect
import stripe

# This is your test secret API key.

import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv('sk')

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

YOUR_DOMAIN = 'http://localhost:4242'

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

# Check Blocked Apartments
@app.route('/blocked_apartments', methods=['POST'])
def check_blocked_apartments():
    date_from = request.json['date_from']
    date_to = request.json['date_to']

    print(date_from, date_to)

    props_request = Pull_ListPropertiesBlocks_RQ(
        username, password, location_id=7912,
        date_from=datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"]),
        date_to=datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    )

    response = requests.post(api_endpoint, data=props_request.serialize_request(), headers={"Content-Type": "application/xml"})
    properties = props_request.check_blocked_properties(response.text, apartment_ids)

    # Fetch prices for available apartments
    prices = Pull_ListPropertyPrices_RQ.get_prices_for_multiple_properties()

    # Merge prices into available properties
    price_map = {
            price_data['property_id']: {
                'price': price_data['price']['Prices']['Season']['Price'],
                'extra': price_data['price']['Prices']['Season']['Extra']
            }
            for price_data in prices
        }

    for apartment in properties['available']:
        apartment['price'] = price_map.get(apartment['id'], 'N/A')  # Default to 'N/A' if no price is found

    return jsonify({'properties': properties})


@app.route('/check_price', methods=['POST'])
def check_price():

    date_from = request.json['date_from']
    date_to = request.json['date_to']
    property_ids = request.json['property_ids']

    print(date_from,date_to,property_ids)
    # Check Apartment Price

    prices = Pull_ListPropertyPrices_RQ.get_prices_for_multiple_properties()

    return prices

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



# @app.route('/create-checkout-session', methods=['POST'])
# def create_checkout_session():
#     try:
#         checkout_session = stripe.checkout.Session.create(
#             line_items=[
#                 {
#                     "price_data": {
#                         "currency": "usd",
#                         "product_data": {
#                             "name": f"Stay from {data['check_in']} to {data['check_out']}",
#                             "description": f"{data['adults']} Adults, {data['children']} Children (Ages: {data['children_ages']})"
#                         },
#                         "unit_amount": int(data['price']) * 100,  # Convert dollars to cents
#                     },
#                     "quantity": 1,
#                 },
#             ],
#             mode='payment',
#             success_url=YOUR_DOMAIN + '/success.html',
#             cancel_url=YOUR_DOMAIN + '/cancel.html',
#         )
#     except Exception as e:
#         return str(e)

#     return redirect(checkout_session.url, code=303)



if __name__ == '__main__':
    app.run()