import requests
from datetime import datetime
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from property_price import Pull_ListPropertyPrices_RQ
from flask import Flask, request, jsonify, redirect
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

# Get today's date and extract year, month, day
today = datetime.now()
day = today.day
month = today.month
year = today.year

# Use all property IDs from apartment_ids
property_ids = list(apartment_ids.keys())

# Update Property Prices File
prices = Pull_ListPropertyPrices_RQ.get_prices_for_multiple_properties_save_to_file(
        username, password, property_ids, 
        date_from=datetime(day=day, month=month, year=year), 
        date_to=datetime(day=day, month=month, year=year) + relativedelta(years=2),
        api_endpoint=api_endpoint
)

print(prices)