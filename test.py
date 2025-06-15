import requests
from datetime import datetime
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from property_price import Pull_ListPropertyPrices_RQ
from flask import Flask, request, jsonify, redirect
from get_booking import Pull_GetReservationByID_RQ
import stripe
from dateutil.relativedelta import relativedelta


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




reservation = Pull_GetReservationByID_RQ(username, password, 143678775)

response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
jsonResponse = reservation.get_details(response.text)
reservation_data = {
    "PropertyID": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"]["PropertyID"],
    "DateFrom": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"]["DateFrom"],
    "DateTo": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"]["DateTo"],
    "ClientPrice": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"]["Costs"]["ClientPrice"],
    "CustomerInfo": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["CustomerInfo"],
    "GuestDetailsInfo": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["GuestDetailsInfo"]
}
print(jsonResponse)
