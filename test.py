import requests
from datetime import datetime
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from property_price import Pull_ListPropertyPrices_RQ
from add_booking import Push_PutConfirmedReservationMulti_RQ
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

# Get today's date and extract year, month, day
today = datetime.now()
day = today.day
month = today.month
year = today.year

# Use all property IDs from apartment_ids
property_ids = list(apartment_ids.keys())

dateFrom = {
    "day": 28,
    "month": 1,
    "year": 2025
}
dateTo = {
    "day": 31,
    "month": 1,
    "year": 2025
}

print(Pull_ListPropertyPrices_RQ.calculate_ru_price(3070533,3,3))

# Update Property Prices File
reservation_with_comments = Push_PutConfirmedReservationMulti_RQ(
    username,
    password,
    property_id=3070533,
    date_from = datetime(day=dateFrom["day"], month=dateFrom["month"], year=dateFrom["year"]),
    date_to= datetime(day=dateTo["day"], month=dateTo["month"], year=dateTo["year"]),
    number_of_guests=4,
    client_price=50.00,
    ru_price=Pull_ListPropertyPrices_RQ.calculate_ru_price(3070533,3,4),
    already_paid=996.00,
    customer_name="Sultan",
    customer_surname="Rasul",
    customer_email="test.test@test.com",
    customer_phone="+11 111 111 111",
    customer_zip_code="00-000",
    number_of_adults=2,
    number_of_children=2,
    children_ages=[12, 9],
    comments="test comment"
)

response = requests.post(api_endpoint, data=reservation_with_comments.serialize_request(), headers={"Content-Type": "application/xml"})

print(response.text)
