import random
import pandas as pd
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import stripe.webhook
from add_booking import Push_PutConfirmedReservationMulti_RQ
from cancel_booking import Push_CancelReservation_RQ
from get_booking import Pull_GetReservationByID_RQ
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from property_price import Pull_ListPropertyPrices_RQ
from flask import Flask, request, jsonify, redirect
import stripe
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time
import re

import traceback
import logging
import google.cloud.logging
# Instantiates a client

import hashlib
from flask_caching import Cache
import json

import os

if os.getenv("ENV") == "production":
    from google.cloud import logging as cloud_logging
    client = cloud_logging.Client()
    client.setup_logging()

from dotenv import load_dotenv

from email_sender import create_email
load_dotenv()


app = Flask(__name__)

# Configure Flask-Caching
cache = Cache(config={'CACHE_TYPE': 'simple'})  # Configure as needed
cache.init_app(app)

def make_cache_key():
    """Generate a unique cache key based on the request payload."""
    data = request.get_json() or {}  # Get request body
    data_string = json.dumps(data, sort_keys=True)  # Convert to string
    return hashlib.md5(data_string.encode()).hexdigest()  # Hash for uniqueness

stripe.api_key = os.getenv('sk')
stripe_webhook_key = os.getenv('whsec')
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

FRONTEND_URL = 'https://www.rosedenedirect.com'
# FRONTEND_URL = 'http://localhost:5173'
BACKEND_URL =  'https://core.rosedenedirect.com'
# BACKEND_URL =  'http://127.0.0.1:5000'


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

# Apartment IDs dictionary
max_guests = {
    # Apartment Number : Max Guests
    1: 6,
    2: 6,
    3: 4,
    4: 3,
    5: 4,
    6: 6,
    7: 4,
    8: 6,
    9: 4,
    10: 6,
}

# API credentials and endpoints
username = os.getenv('username')
password = os.getenv('password')
api_endpoint = "https://new.rentalsunited.com/api/handler.ashx"

# This gives back the availability of all properties within the users date range
@app.route('/blocked_apartments', methods=['POST'])
# @cache.memoize(timeout=300)
def check_blocked_apartments():


    try:
        date_from = request.json['date_from']
        date_to = request.json['date_to']
        try:
            date_from = request.json['date_from']
            date_to = request.json['date_to']
            date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
            date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
        except Exception:
            return jsonify({"error": "Invalid date format"}), 400
        
        props_request = Pull_ListPropertiesBlocks_RQ(
            username, password, location_id=7912,
            date_from=date_from_obj,
            date_to=date_to_obj
        )

        response = requests.post(api_endpoint, data=props_request.serialize_request(), headers={"Content-Type": "application/xml"})
        properties = props_request.check_blocked_properties(response.text, apartment_ids)

        # Fetch prices for available apartments
        prices = Pull_ListPropertyPrices_RQ.get_all_prices()

        if not props_request or "available" not in properties:
            return jsonify({"error": "Apartment is blocked for selected dates"}), 400
            
        # Now add the prices to each apartment and include the overlap logic
        for apartment in properties['available']:
            apartment_prices = prices[str(apartment['id'])]
            if apartment_prices['Prices']:
                apartment['Prices'] = apartment_prices['Prices']  # Add the list of prices for this apartment
            else:
                apartment['Prices'] = 'N/A'  # Default to 'N/A' if no price is found

        # Now add the prices to each apartment and include the overlap logic
        for apartment in properties['blocked']:
            apartment_prices = prices[str(apartment['id'])]
            if apartment_prices['Prices']:
                apartment['Prices'] = apartment_prices['Prices']  # Add the list of prices for this apartment
            else:
                apartment['Prices'] = 'N/A'  # Default to 'N/A' if no price is found

        print(properties)

        return jsonify({'properties': properties})
    
    except Exception as e:
        logging.error(f"Error checking blocks: {e}")
        return False

@app.route('/check_price', methods=['POST'])
def check_price():
    try:
        property_id = request.json.get('property_id')

        if not property_id:
            
            logging.error(f"❌ Missing property_id")
            return jsonify({"error": "Missing property_id"}), 400

        # Get all prices
        all_prices = Pull_ListPropertyPrices_RQ.get_all_prices()
        if not all_prices or str(property_id) not in all_prices:
            logging.error(f"❌ No price data found for this property")
            return jsonify({"error": "No price data found for this property"}), 404

        prices = all_prices[str(property_id)]

        # Safely extract Seasons
        property_prices = prices.get("Prices", {})
        seasons = property_prices.get("Season")

        if not seasons:
            return jsonify({"error": "No seasonal pricing information available"}), 404

        return prices

    except Exception as e:
        logging.error(f"❌ Error in check_price: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/verify_price', methods=['POST'])
def verify_price():
    try:
        # Validate required parameters exist
        required_fields = ['property_id', 'refundable', 'date_from', 'date_to', 'adults', 'children']
        if not all(field in request.json for field in required_fields):
            missing = [field for field in required_fields if field not in request.json]
            logging.error(f"❌ Missing parameters: {', '.join(missing)}")
            return jsonify({"error": f"Missing required parameters: {', '.join(missing)}"}), 400

        # Extract parameters
        data = request.json
        property_id = data['property_id']
        refundable = data['refundable']
        date_from = data['date_from']
        date_to = data['date_to']
        adults = data['adults']
        children = data['children']

        # Validate dates structure
        date_fields = ['day', 'month', 'year']
        if not all(key in date_from for key in date_fields) or not all(key in date_to for key in date_fields):
            logging.error("❌ Invalid date format")
            return jsonify({"error": "Date objects must contain day, month, and year"}), 400

        # Create date objects
        try:
            date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
            date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
        except ValueError as e:
            logging.error(f"❌ Invalid date values: {e}")
            return jsonify({"error": "Invalid date values"}), 400

        # Validate date range
        if date_to_obj <= date_from_obj:
            logging.error("❌ Invalid date range: date_to must be after date_from")
            return jsonify({"error": "date_to must be after date_from"}), 400

        # Validate guests
        try:
            adults = int(adults)
            children = int(children)
            if adults < 0 or children < 0:
                raise ValueError
        except ValueError:
            logging.error("❌ Invalid guest counts: must be positive integers")
            return jsonify({"error": "adults and children must be positive integers"}), 400

        # Calculate nights
        nights = (date_to_obj - date_from_obj).days
        if nights < 2:
            logging.error("❌ Invalid stay duration: 0 nights")
            return jsonify({"error": "Stay must be at least 2 night"}), 400

        # Verify property exists
        all_prices = Pull_ListPropertyPrices_RQ.get_all_prices()
        if not all_prices or str(property_id) not in all_prices:
            logging.error(f"❌ Property not found: {property_id}")
            return jsonify({"error": "Property not found"}), 404

        # Calculate prices
        try:
            base_price = Pull_ListPropertyPrices_RQ.calculate_ru_price(
                property_id=property_id,
                guests=(adults + children),
                date_from=date_from_obj,
                date_to=date_to_obj
            )
            
            client_price = Pull_ListPropertyPrices_RQ.calculate_client_price(
                basePrice=base_price,
                refundable=refundable
            )
        except Exception as e:
            logging.error(f"❌ Price calculation failed: {e}")
            return jsonify({"error": "Price calculation error"}), 500

        # Build breakdown
        per_night_price = round(base_price / nights, 2)
        breakdown = [{
            "label": f"£{per_night_price:.2f} x {nights} nights",
            "amount": round(base_price, 2)
        }]

        if refundable:
            try:
                refund_fee = Pull_ListPropertyPrices_RQ.calculate_refundable_rate_fee(base_price)
                breakdown.append({
                    "label": "Refundable rate",
                    "amount": f"{refund_fee:.2f}"
                })
            except Exception as e:
                logging.error(f"❌ Refund fee calculation failed: {e}")
                return jsonify({"error": "Refund fee calculation error"}), 500

        return jsonify({
            "total": f"{client_price:.2f}",
            "breakdown": breakdown
        })

    except Exception as e:
        logging.error(f"❌ Unhandled error in verify_price: {e}")
        return jsonify({"error": "Internal server error"}), 500

# This gives back the specific apartment availability for the next 2 years
@app.route('/check_calendar', methods=['POST'])
def check_calendar():
    try:
        # Validate required parameters
        if 'property_id' not in request.json:
            logging.error("❌ Missing property_id in request")
            return jsonify({"error": "Missing property_id"}), 400

        property_id = request.json['property_id']
        
        # Create date range
        date_from = datetime.today()
        date_to = date_from + relativedelta(years=5)

        # Validate property ID format
        try:
            # Ensure property_id is integer-convertible
            int(property_id)
        except ValueError:
            logging.error(f"❌ Invalid property_id format: {property_id}")
            return jsonify({"error": "property_id must be an integer"}), 400

        # Make API request
        try:
            avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
                username, password, property_id=property_id,
                date_from=date_from, 
                date_to=date_to
            )
            response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})  # Added timeout
            
            # Check HTTP status
            if response.status_code != 200:
                logging.error(f"❌ API returned {response.status_code}: {response.text}")
                return jsonify({"error": "Calendar service unavailable"}), 503
                
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ API connection failed: {e}")
            return jsonify({"error": "Calendar service unavailable"}), 503
        except Exception as e:
            logging.error(f"❌ Request serialization failed: {e}")
            return jsonify({"error": "Request processing error"}), 500

        # Process response
        try:
            calendar = avail_request.check_availability_calendar(response.text)
            if not calendar:
                logging.error(f"❌ Empty calendar data for property {property_id}")
                return jsonify({"error": "No calendar data available"}), 404
                
            return jsonify(calendar)
            
        except Exception as e:
            logging.error(f"❌ Calendar parsing failed: {e}")
            return jsonify({"error": "Calendar data processing error"}), 500

    except Exception as e:
        logging.error(f"❌ Unhandled error in check_calendar: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    try:
        # Validate request format
        if not request.is_json:
            logging.error("❌ Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        required_fields = [
            "date_from", "date_to", "property_id", "adults", "children", 
            "childrenAges", "refundable", "name", "phone", "email", "special_requests"
        ]

        # Validate required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logging.error(f"❌ Missing fields: {', '.join(missing_fields)}")
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Validate property ID
        try:
            property_id = int(data['property_id'])
            if property_id not in apartment_ids:
                logging.error(f"❌ Invalid property ID: {property_id}")
                return jsonify({"error": "Invalid property ID"}), 400
        except (ValueError, TypeError):
            logging.error(f"❌ Invalid property ID format: {data['property_id']}")
            return jsonify({"error": "property_id must be an integer"}), 400

        # Validate dates
        try:
            date_from = data['date_from']
            date_to = data['date_to']
            date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
            date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
            
            # Validate date range
            if date_to_obj <= date_from_obj:
                logging.error("❌ Invalid date range: date_to must be after date_from")
                return jsonify({"error": "date_to must be after date_from"}), 400
                
            nights = (date_to_obj - date_from_obj).days
            if nights < 2:
                logging.error("❌ Invalid stay duration: must be at least 2 night")
                return jsonify({"error": "Stay must be at least 2 night"}), 400
                
        except KeyError as e:
            logging.error(f"❌ Missing date component: {e}")
            return jsonify({"error": "Date objects must contain day, month, and year"}), 400
        except ValueError as e:
            logging.error(f"❌ Invalid date values: {e}")
            return jsonify({"error": "Invalid date values"}), 400

        # Validate guest counts
        try:
            adults = int(data['adults'])
            children = int(data['children'])
            childrenAges = data['childrenAges']
            
            if adults <= 0:
                logging.error("❌ Adults count must be at least 1")
                return jsonify({"error": "At least 1 adult required"}), 400
                
            if children < 0:
                logging.error("❌ Children count cannot be negative")
                return jsonify({"error": "Children count cannot be negative"}), 400
                
            if children > 0 and (not isinstance(childrenAges, list) or len(childrenAges) != children):
                logging.error("❌ Children ages array size doesn't match children count")
                return jsonify({"error": "Children ages array size must match children count"}), 400
                
            total_guests = adults + children
        except (ValueError, TypeError):
            logging.error("❌ Invalid guest counts format")
            return jsonify({"error": "adults and children must be integers"}), 400

        # Validate contact info
        name = data['name'].strip()
        phone = data['phone'].strip()
        email = data['email'].strip()
        specialRequests = data['special_requests']
        
        if not name:
            logging.error("❌ Name cannot be empty")
            return jsonify({"error": "Name cannot be empty"}), 400
            
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            logging.error(f"❌ Invalid email format: {email}")
            return jsonify({"error": "Invalid email format"}), 400

        # Validate refundable type
        try:
            refundable = bool(data['refundable'])
        except ValueError:
            logging.error("❌ Invalid refundable value")
            return jsonify({"error": "refundable must be boolean"}), 400

        # Validate maximum guests
        try:
            apartment_number = int(apartment_ids[property_id].split()[-1])
            max_allowed = max_guests.get(apartment_number)
            
            if not max_allowed:
                logging.error(f"❌ No max guest limit configured for property {property_id}")
                return jsonify({"error": "Property configuration error"}), 500
                
            if total_guests > max_allowed:
                logging.error(f"❌ Exceeds max guests: {total_guests} > {max_allowed}")
                return jsonify({"error": f"Max guests allowed: {max_allowed}"}), 400
        except Exception as e:
            logging.error(f"❌ Max guest validation failed: {e}")
            return jsonify({"error": "Guest limit validation error"}), 500

        # Check availability
        try:
            avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
                username, password, property_id=property_id,
                date_from=date_from_obj, 
                date_to=date_to_obj
            )
            response = requests.post(api_endpoint, data=avail_request.serialize_request(),  headers={"Content-Type": "application/xml"})
                                   
            if response.status_code != 200:
                logging.error(f"❌ Availability API failed: {response.status_code}")
                return jsonify({"error": "Availability service unavailable"}), 503
                
            calendar = avail_request.check_availability_calendar(response.text)
            
            for day in calendar:
                if day.get("IsBlocked") == "true":
                    logging.error(f"❌ Property blocked on {day.get('Date')}")
                    return jsonify({"error": "Apartment not available for selected dates"}), 409
                    
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Availability API connection failed: {e}")
            return jsonify({"error": "Availability service unavailable"}), 503
        except Exception as e:
            logging.error(f"❌ Availability check failed: {e}")
            return jsonify({"error": "Availability check error"}), 500

        # Calculate price
        try:
            basePrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(
                property_id=property_id, 
                guests=total_guests,
                date_from=date_from_obj, 
                date_to=date_to_obj
            )
            
            if basePrice <= 0:
                logging.error(f"❌ Invalid base price: {basePrice}")
                return jsonify({"error": "Pricing error"}), 500
                
            customerPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(
                basePrice=basePrice, 
                refundable=refundable
            )
            
            if customerPrice <= 0:
                logging.error(f"❌ Invalid customer price: {customerPrice}")
                return jsonify({"error": "Pricing calculation error"}), 500
        except Exception as e:
            logging.error(f"❌ Price calculation failed: {e}")
            return jsonify({"error": "Price calculation error"}), 500

        # Create payment intent
        try:
            display_date = f'{date_from["day"]}/{date_from["month"]}/{date_from["year"]} - {date_to["day"]}/{date_to["month"]}/{date_to["year"]}'
            description = f"{display_date} • {adults} Adult{'s' if adults > 1 else ''}"
            if children > 0:
                description += f" • {children} Child{'ren' if children != 1 else ''}"
            
            payment_intent = stripe.PaymentIntent.create(
                amount=int(customerPrice * 100),
                currency='gbp',
                payment_method_types=['card'],
                metadata={
                    "apartment_id": property_id,
                    "apartment_name": apartment_ids[property_id],
                    "date_from": f"{date_from['day']}/{date_from['month']}/{date_from['year']}",
                    "date_to": f"{date_to['day']}/{date_to['month']}/{date_to['year']}",
                    "adults": adults,
                    "children": children,
                    "children_ages": ",".join(str(age) for age in childrenAges),
                    "nights": nights,
                    "price": customerPrice,
                    "name": name,
                    "email": email,
                    "phone_number": phone,
                    "special_requests": specialRequests,
                    "refundable": refundable,
                    "booking_reference": "",
                },
                description=f"Booking for {apartment_ids[property_id]}",
                capture_method='manual'
            )
        except stripe.error.StripeError as e:
            logging.error(f"❌ Stripe API error: {e.user_message if hasattr(e, 'user_message') else str(e)}")
            return jsonify({"error": "Payment processing error"}), 500
        except Exception as e:
            logging.error(f"❌ Payment intent creation failed: {e}")
            return jsonify({"error": "Payment processing error"}), 500

        # Log successful request
        logging.info({
            "severity": "INFO",
            "message": "Create Checkout Request",
            "payment_intent_id": payment_intent.id,
            "property_id": property_id,
            "guests": total_guests,
            "refundable": refundable,
            "date_from": str(date_from_obj),
            "date_to": str(date_to_obj),
            "client_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
        })
        return jsonify({
            'clientSecret': payment_intent.client_secret,
            'amount': f"{customerPrice:.2f}"
        })
    
    except Exception as e:
        logging.error(f"❌ Unhandled error in create_checkout: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/update-guest-info', methods=['POST'])
def update_guest_info():
    try:
        # Validate request format
        if not request.is_json:
            logging.error("❌ Request is not JSON")
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        
        # Validate required field
        if 'client_secret' not in data or not data['client_secret']:
            logging.error("❌ Missing client_secret")
            return jsonify({"error": "Missing client_secret"}), 400
            
        client_secret = data['client_secret'].strip()
        
        # Validate client_secret format
        if '_secret' not in client_secret:
            logging.error(f"❌ Invalid client_secret format: {client_secret}")
            return jsonify({"error": "Invalid client_secret format"}), 400

        try:
            # Extract payment intent ID
            payment_intent_id = client_secret.split("_secret")[0]
            
            # Validate payment intent ID format
            if not payment_intent_id.startswith('pi_') or len(payment_intent_id) < 8:
                logging.error(f"❌ Invalid payment intent ID format: {payment_intent_id}")
                return jsonify({"error": "Invalid payment intent ID"}), 400
                
        except (IndexError, TypeError, AttributeError):
            logging.error(f"❌ Failed to extract payment intent ID from: {client_secret}")
            return jsonify({"error": "Invalid client_secret format"}), 400

        # Prepare metadata - minimal sanitization
        metadata = {}
        if 'name' in data:
            metadata['name'] = str(data['name']).strip()[:500]
        if 'phone' in data:
            metadata['phone_number'] = str(data['phone']).strip()[:50]
        if 'email' in data:
            metadata['email'] = str(data['email']).strip()[:320]
        if 'special_requests' in data:
            metadata['special_requests'] = str(data['special_requests']).strip()[:1000]

        if not metadata:
            logging.error("❌ No valid fields to update")
            return jsonify({"error": "No valid fields to update"}), 400

        # Update metadata with Stripe
        try:
            stripe.PaymentIntent.modify(
                payment_intent_id,
                metadata=metadata
            )
            
            # Log successful update
            logging.info({
                "severity": "INFO",
                "message": "Updated Guest Information At Checkout",
                "payment_intent_id": payment_intent_id,
                "updated_fields": list(metadata.keys()),
                "client_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
            })

            return jsonify({"message": "Guest info updated successfully"}), 200

        except stripe.error.StripeError as e:
            # Handle specific Stripe errors
            error_type = type(e).__name__
            user_message = e.user_message if hasattr(e, 'user_message') else "Payment processing error"
            
            logging.error(f"❌ Stripe API error ({error_type}): {str(e)}")
            return jsonify({"error": user_message}), 400
            
        except Exception as e:
            logging.error(f"❌ Stripe update failed: {str(e)}")
            return jsonify({"error": "Payment update failed"}), 500

    except Exception as e:
        logging.error(f"❌ Unhandled error in update_guest_info: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    try:
        # Validate request format
        if not request.is_json:
            logging.warning({
                "message": "Request is not JSON",
                "severity": "WARNING"
            })
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.json
        booking_ref = data.get('booking_ref')
        email = data.get('email')
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Validate required parameters
        if not booking_ref or not email:
            logging.warning({
                "message": "Missing booking_ref or email",
                "booking_ref": booking_ref,
                "ip": user_ip,
                "severity": "WARNING"
            })
            return jsonify({'error': 'Both booking_ref and email are required'}), 400

        # Sanitize inputs
        booking_ref = str(booking_ref).strip()
        email = str(email).strip().lower()

        logging.info({
            "message": "Cancellation attempt received",
            "booking_ref": booking_ref,
            "ip": user_ip,
            "severity": "INFO"
        })

        # Get booking details from Rentals United
        try:
            reservation = Pull_GetReservationByID_RQ(username, password, booking_ref)
            response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
            
            if response.status_code != 200:
                logging.error({
                    "message": "Rentals United API failed",
                    "status_code": response.status_code,
                    "booking_ref": booking_ref,
                    "severity": "ERROR"
                })
                return jsonify({'error': 'Reservation service unavailable'}), 503
            
            booking_data = reservation.get_details(response.text)
        except Exception as e:
            logging.exception(f"❌ Failed to fetch booking details for {booking_ref}")
            return jsonify({'error': 'Failed to retrieve booking details'}), 500

        # Validate RU response structure
        try:
            status_info = booking_data["Pull_GetReservationByID_RS"]["Status"]
            status_code = int(status_info["@ID"])
            status_text = status_info["#text"]

            if status_code != 0:
                logging.warning({
                    "message": "Reservation lookup failed",
                    "status_code": status_code,
                    "status_text": status_text,
                    "booking_ref": booking_ref,
                    "severity": "WARNING"
                })
                return jsonify({'error': status_text}), 420 if status_code == 28 else 400

            # Extract reservation data
            reservation_data = booking_data["Pull_GetReservationByID_RS"]["Reservation"]
            reservationID = reservation_data["ReservationID"]
            rentalsUnitedCommentsJson = json.loads(reservation_data["Comments"])
            
            # Extract customer info
            customer_info = reservation_data["CustomerInfo"]
            bookingEmail = customer_info["Email"].lower()
            name = customer_info["Name"]
            phone = customer_info["Phone"]
            
            # Extract booking info
            booking_info = reservation_data["StayInfos"]["StayInfo"]
            dateFrom = booking_info.get("DateFrom")
            dateTo = booking_info.get("DateTo")
            
            # Validate dates
            date_from_obj = datetime.strptime(dateFrom, "%Y-%m-%d")
            date_to_obj = datetime.strptime(dateTo, "%Y-%m-%d")
            nights = (date_to_obj - date_from_obj).days
            
            if nights <= 0:
                logging.error({
                    "message": "Invalid date range in booking",
                    "dateFrom": dateFrom,
                    "dateTo": dateTo,
                    "booking_ref": booking_ref,
                    "severity": "ERROR"
                })
                return jsonify({'error': 'Invalid booking date range'}), 500
                
            apartmentID = int(booking_info.get("PropertyID"))
            
            # Extract guest info
            guest_info = reservation_data["GuestDetailsInfo"]
            adults = int(guest_info["NumberOfAdults"])
            children = int(guest_info["NumberOfChildren"])
            
            # Extract children ages
            childrenAges = []
            if children > 0:
                age_data = guest_info.get("ChildrenAges", {}).get("Age", [])
                if isinstance(age_data, list):
                    childrenAges = age_data
                elif isinstance(age_data, str):
                    childrenAges = [age_data]
                    
            # Validate email match
            if email != bookingEmail:
                logging.warning({
                    "message": "Email mismatch during cancellation",
                    "submitted_email": email,
                    "booking_email": bookingEmail,
                    "booking_ref": booking_ref,
                    "severity": "WARNING"
                })
                return jsonify({'error': 'Email does not match booking'}), 420
                
            # Get payment details
            refundable = rentalsUnitedCommentsJson.get("refundable", False)
            paymentIntentId = rentalsUnitedCommentsJson.get("paymentIntentId")
            specialRequest = rentalsUnitedCommentsJson.get("specialRequest")
            
        except (KeyError, TypeError, ValueError) as e:
            logging.exception(f"❌ Error parsing booking data for {booking_ref}")
            return jsonify({'error': 'Invalid booking data format'}), 500

        # Cancel in Rentals United
        try:
            cancel = Push_CancelReservation_RQ(username, password, booking_ref, cancel_type_id=2)
            cancel_response = requests.post(api_endpoint, data=cancel.serialize_request(), headers={"Content-Type": "application/xml"})
            
            if cancel_response.status_code != 200:
                logging.error({
                    "message": "Rentals United cancel API failed",
                    "status_code": cancel_response.status_code,
                    "booking_ref": booking_ref,
                    "severity": "ERROR"
                })
                return jsonify({'error': 'Cancel service unavailable'}), 503
                
            cancel_data = reservation.get_details(cancel_response.text)
            cancel_status = int(cancel_data["Push_CancelReservation_RS"]["Status"]["@ID"])
            cancel_text = cancel_data["Push_CancelReservation_RS"]["Status"]["#text"]

            if cancel_status != 0:
                logging.error({
                    "message": "Failed to cancel reservation in Rentals United",
                    "booking_ref": booking_ref,
                    "status": cancel_status,
                    "error": cancel_text,
                    "severity": "ERROR"
                })
                return jsonify({'error': f'Cancel failed: {cancel_text}'}), 500
                
        except Exception as e:
            logging.exception(f"❌ Exception cancelling RU booking {booking_ref}")
            return jsonify({'error': f'Failed to cancel reservation: {str(e)}'}), 500

        # Calculate days until check-in
        today = datetime.today()
        diffDays = (date_from_obj - today).days

        # Process refund if applicable
        refund_successful = False
        if refundable and diffDays >= 13 and paymentIntentId:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(paymentIntentId, expand=["charges"])
                charge_id = payment_intent.latest_charge

                if not charge_id:
                    raise Exception("No charge found for PaymentIntent")

                refund = stripe.Refund.create(charge=charge_id, reason='requested_by_customer')
                refund_successful = refund.status == "succeeded"
                
                if not refund_successful:
                    raise Exception(f"Refund status: {refund.status}")
                    
                logging.info({
                    "message": "Stripe refund successful",
                    "payment_intent_id": paymentIntentId,
                    "charge_id": charge_id,
                    "refund_status": refund.status,
                    "severity": "INFO"
                })
            except Exception as e:
                logging.exception(f"❌ Refund failed for payment intent {paymentIntentId}")
                # Continue even if refund fails - booking is already cancelled in RU
                # Consider adding an alert for manual follow-up

        # Send cancellation email
        try:
            # Calculate price for email
            ruPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(
                property_id=apartmentID, 
                guests=(adults+children),
                date_from=date_from_obj,
                date_to=date_to_obj
            )
            
            clientPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(
                basePrice=ruPrice, 
                refundable=refundable
            )
            
            # Build price breakdown
            breakdown = []
            if nights > 0:
                per_night_price = round(ruPrice/nights, 2)
                breakdown.append({
                    "label": f"£{per_night_price} x {nights} nights",
                    "amount": round(ruPrice, 2)
                })
                
                if refundable:
                    refundable_rate_fee = Pull_ListPropertyPrices_RQ.calculate_refundable_rate_fee(ruPrice)
                    breakdown.append({
                        "label": "Refundable rate",
                        "amount": refundable_rate_fee
                    })
            
            # Generate HTML rows for email
            breakdown_html_rows = ""
            for index, item in enumerate(breakdown):
                label = item["label"]
                amount = f"£{item['amount']:.2f}"
                breakdown_html_rows += f"""
                    <tr>
                        <td style="color:#4b5563; font-size:15px;">{label}</td>
                        <td align="right" style="color:#374151; font-size:16px;">{amount}</td>
                    </tr>
                """
                if index < len(breakdown) - 1:
                    breakdown_html_rows += """
                    <tr>
                        <td colspan="2" height="15"></td>
                    </tr>
                    """
            
            # Format dates for email
            date_from_str = f"{date_from_obj.day} {date_from_obj.strftime('%b')} {date_from_obj.year}"
            date_to_str = f"{date_to_obj.day} {date_to_obj.strftime('%b')} {date_to_obj.year}"
            
            # Create and send email
            email_sender = create_email(
                name=name,
                # breakdown_html_rows=breakdown_html_rows,
                ruPrice=ruPrice,
                clientPrice=clientPrice,
                booking_reference=reservationID,
                date_from=date_from_str,
                date_to=date_to_str,
                apartmentName=apartment_ids.get(apartmentID, "Unknown Property"),
                phone=phone,
                adults=adults,
                children=children,
                childrenAges=childrenAges,
                nights=nights,
                refundable=refundable,
                email=email,
                specialRequests=specialRequest,
                cancel=True,
                diffDays=diffDays
            )
            email_sender.send_email(os.getenv('email'))

            logging.info({
                "message": "Cancellation email sent",
                "booking_ref": booking_ref,
                "email": email,
                "severity": "INFO"
            })
        except Exception as e:
            logging.exception(f"❌ Failed to send cancellation email for {booking_ref}")
            # Continue even if email fails - cancellation is already processed

        return jsonify({
            'message': 'Booking cancelled successfully',
            'refund_attempted': refundable and diffDays >= 13,
            'refund_successful': refund_successful
        })

    except Exception as e:
        logging.exception("🔥 Uncaught error in cancel_booking route")
        return jsonify({'error': 'Something went wrong processing the cancel request'}), 500
    
def cancel_payment_intent_with_error(payment_intent_id, error_code, error_text):
    try:
        stripe.PaymentIntent.modify(
            payment_intent_id,
            metadata={
                "error_code": error_code,
                "error_text": error_text
            }
        )
        stripe.PaymentIntent.cancel(
            payment_intent_id,
            cancellation_reason="booking_failed"
        )
        logging.info(f"❌ PaymentIntent {payment_intent_id} cancelled due to: {error_code} - {error_text}")
    except Exception as e:
        logging.exception(f"⚠️ Failed to cancel or update metadata for PaymentIntent {payment_intent_id}")    

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Validate payload and signature
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            logging.error("⚠️ Missing Stripe-Signature header")
            return jsonify({"error": "Missing signature"}), 400

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, stripe_webhook_key)
        except ValueError as e:
            logging.exception("⚠️ Invalid payload")
            return jsonify({"error": "Invalid payload"}), 400
        except stripe.error.SignatureVerificationError as e:
            logging.exception("⚠️ Invalid signature")
            return jsonify({"error": "Invalid signature"}), 400

        # Only handle charge.succeeded events
        if event['type'] != 'charge.succeeded':
            logging.info({
                "message": "Ignored Stripe webhook event",
                "event_type": event['type'],
            })
            return jsonify({"message": "Event ignored"}), 200

        try:
            # Handle the event
            charge_obj = event['data']['object']
            payment_intent_id = charge_obj.get("payment_intent")
            
            if not payment_intent_id:
                logging.error("⚠️ Charge object missing payment_intent")
                return jsonify({"error": "Invalid charge object"}), 400

            # Retrieve full payment intent
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            except stripe.error.StripeError as e:
                logging.exception(f"⚠️ Failed to retrieve PaymentIntent {payment_intent_id}")
                return jsonify({"error": "Payment intent retrieval failed"}), 400

            # Extract metadata safely
            meta_data = payment_intent.get('metadata', {})
            required_fields = ["adults", "children", "apartment_id", "refundable", 
                              "date_from", "date_to", "nights"]
            
            missing_fields = [field for field in required_fields if field not in meta_data]
            if missing_fields:
                logging.error(f"⚠️ Missing metadata fields: {', '.join(missing_fields)}")
                cancel_payment_intent_with_error(payment_intent_id, -1, f"⚠️ Missing metadata fields: {', '.join(missing_fields)}")
                return jsonify({"error": f"Missing required metadata: {', '.join(missing_fields)}"}), 400

            try:
                # Parse metadata values
                adults = int(meta_data["adults"])
                apartment_id = int(meta_data["apartment_id"])
                refundable = meta_data["refundable"].lower() == "true"
                children = int(meta_data["children"])
                nights = int(meta_data["nights"])
                
                # Parse dates
                try:
                    date_from_obj = datetime.strptime(meta_data["date_from"], "%d/%m/%Y")
                    date_to_obj = datetime.strptime(meta_data["date_to"], "%d/%m/%Y")
                except ValueError as e:
                    logging.exception(f"⚠️ Invalid date format in metadata")
                    cancel_payment_intent_with_error(payment_intent_id, -1, "⚠️ Invalid date format in metadata")
                    return jsonify({"error": "Invalid date format"}), 400
                
                # Validate date range
                if (date_to_obj - date_from_obj).days != nights:
                    logging.error(f"⚠️ Date range doesn't match nights: {nights}")
                    cancel_payment_intent_with_error(payment_intent_id, -1, f"⚠️ Date range doesn't match nights: {nights}")
                    return jsonify({"error": "Date range mismatch"}), 400
                    
                # Process children ages
                childrenAges = []
                if children > 0:
                    children_ages_str = meta_data.get("children_ages", "")
                    if children_ages_str:
                        childrenAges = children_ages_str.split(",")
                    if len(childrenAges) != children:
                        logging.warning(f"⚠️ Children ages count mismatch: expected {children}, got {len(childrenAges)}")
                        childrenAges = childrenAges[:children]  # Truncate to match count
                
                special_requests = meta_data.get("special_requests", "")
                name = meta_data.get("name", "")
                phone = meta_data.get("phone_number", "")
                email = meta_data.get("email", "")
                
                # Get billing details as fallback
                billing_details = charge_obj.get('billing_details', {})
                name = name or billing_details.get("name", "")
                phone = phone or billing_details.get("phone", "")
                email = email or billing_details.get("email", "")
                country = billing_details.get("address", {}).get("country", "")
                postal_code = billing_details.get("address", {}).get("postal_code", "")
                
                # Validate contact info
                if not name:
                    logging.error("⚠️ Missing guest name")
                    cancel_payment_intent_with_error(payment_intent_id, -1, f"⚠️ Missing guest name")
                    return jsonify({"error": "Missing guest name"}), 400
                if not email:
                    logging.error("⚠️ Missing email")
                    cancel_payment_intent_with_error(payment_intent_id, -1, f"⚠️ Missing email")
                    return jsonify({"error": "Missing email"}), 400

            except (ValueError, TypeError) as e:
                logging.exception("⚠️ Metadata parsing error")
                cancel_payment_intent_with_error(payment_intent_id, -1, f"⚠️ Metadata parsing error")
                return jsonify({"error": "Invalid metadata values"}), 400

            # Calculate prices
            try:
                ruPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(
                    property_id=apartment_id, 
                    guests=(adults+children),
                    date_from=date_from_obj,
                    date_to=date_to_obj
                )
                
                clientPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(
                    basePrice=ruPrice, 
                    refundable=refundable
                )
            except Exception as e:
                logging.exception("⚠️ Price calculation failed")
                cancel_payment_intent_with_error(payment_intent_id, -1, f"⚠️ Price calculation failed")
                return jsonify({"error": "Price calculation error"}), 500

            # Prepare booking data for RU
            booking_data = {
                "adults": adults,
                "children": children,
                "childrenAges": childrenAges,
                "specialRequest": special_requests,
                "refundable": refundable,
                "paymentIntentId": payment_intent_id,
                "country": country
            }
            booking_info = json.dumps(booking_data, indent=2)

            # Add Booking to Rentals United
            try:
                reservation = Push_PutConfirmedReservationMulti_RQ(
                    username,
                    password,
                    property_id=apartment_id,
                    date_from=date_from_obj,
                    date_to=date_to_obj,
                    number_of_guests=adults+children,
                    client_price=clientPrice,
                    ru_price=ruPrice,
                    already_paid=clientPrice,
                    customer_name=name,
                    customer_surname=" ",  # RU requires surname
                    customer_email=email,
                    customer_phone=phone,
                    customer_zip_code=postal_code,
                    number_of_adults=adults,
                    number_of_children=children,
                    children_ages=childrenAges,
                    comments=booking_info,
                    commission=0
                )
                
                # Send request to RU with timeout
                response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
                
                if response.status_code != 200:
                    logging.error(f"⚠️ RU API failed with status {response.status_code}")
                    
                    cancel_payment_intent_with_error(payment_intent_id, status_code, "⚠️ RU API failed")


                    return jsonify({"error": "Reservation service unavailable"}), 503
                
                jsonResponse = reservation.booking_reference(response.text)
            except Exception as e:
                logging.exception("⚠️ RU reservation creation failed")

                cancel_payment_intent_with_error(payment_intent_id, status_code, "⚠️ RU reservation creation failed")

                return jsonify({"error": "Reservation creation failed"}), 500

            # Process RU response
            try:
                status_info = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["Status"]
                status_code = int(status_info["@ID"])
                status_text = status_info["#text"]

                if status_code != 0:
                    # Cancel payment intent if RU fails
                    try:

                        cancel_payment_intent_with_error(payment_intent_id, status_code, status_text)

                    except Exception as e:
                        logging.exception(f"⚠️ Failed to cancel payment intent {payment_intent_id}")

                    logging.error(f"⚠️ RU booking failed: {status_text} (code {status_code})")
                    return jsonify({"error": status_text}), 409
                    
                booking_reference = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]
            except (KeyError, TypeError) as e:
                logging.exception("⚠️ Invalid RU response format")
                return jsonify({"error": "Invalid reservation response"}), 500

            # Capture payment and update metadata
            try:
                stripe.PaymentIntent.modify(
                    payment_intent_id,
                    metadata={"booking_reference": booking_reference}
                )
                captured_intent = stripe.PaymentIntent.capture(payment_intent_id)
                
                if captured_intent.status != 'succeeded':
                    raise Exception(f"Capture status: {captured_intent.status}")
                    
                logging.info({
                    "message": "✅ Booking confirmed",
                    "booking_reference": booking_reference,
                    "payment_intent_id": payment_intent_id 
                })
            except stripe.error.StripeError as e:
                logging.exception(f"⚠️ Payment capture failed for {payment_intent_id}")
                # Critical error - booking created but payment not captured!
                # Add alerting here (email/sms to admin)
                return jsonify({"error": "Payment capture failed"}), 500

            # Prepare email content
            
            # Calculate days until check-in
            today = datetime.today()
            diffDays = (date_from_obj - today).days

            # Send confirmation email
            try:
                apartment_name = apartment_ids.get(apartment_id, f"Apartment {apartment_id}")
                
                email_sender = create_email(
                    name=name,
                    # breakdown_html_rows=breakdown_html_rows,
                    clientPrice=clientPrice,
                    ruPrice=ruPrice,
                    booking_reference=booking_reference,
                    date_from=date_from_obj.strftime("%d %b %Y"),
                    date_to=date_to_obj.strftime("%d %b %Y"),
                    apartmentName=apartment_name,
                    phone=phone,
                    adults=adults,
                    children=children,
                    childrenAges=childrenAges,
                    nights=nights,
                    refundable=refundable,
                    email=email,
                    specialRequests=special_requests,
                    cancel=False,
                    diffDays=diffDays
                )
                email_sender.send_email(os.getenv('email'))
                logging.info({
                    "message": "📧 Booking email sent",
                    "booking_reference": booking_reference
                })
            except Exception as email_error:
                logging.exception(f"⚠️ Failed to send booking email for {booking_reference}")

            return jsonify({
                "message": "Booking completed", 
                "reference": booking_reference
            }), 200
            
        except Exception as e:
            logging.exception("🔥 Error processing charge.succeeded event")
            return jsonify({"error": "Event processing error"}), 500

    except Exception as e:
        logging.exception("🔥 Unhandled error in webhook")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/payment-status', methods=['POST'])
def check_payment_status():
    try:

        data = request.json
        payment_intent_id = data["payment_intent_id"]
        email = data["email"]

        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        metadata = payment_intent.metadata
        status = payment_intent.status
        

        if 'booking_reference' in metadata and status == "succeeded" and email == metadata["email"]:
            return jsonify({
                "status": "confirmed",
                "booking_reference": metadata["booking_reference"],
                "email": metadata["email"],
            })
        elif 'booking_reference' in metadata and status == "canceled" and email == metadata["email"]:
            return jsonify({
                "status": metadata["error_code"],
                "error": metadata["error_text"]
            }), 420
        elif 'booking_reference' in metadata and email == metadata["email"]:
            return jsonify({
                "status": "pending"
            })
        else:
            return jsonify({
                "status": "Booking Not Found"
            }), 403
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_booking', methods=['POST'])
def get_booking():
    booking_ref = request.json.get('booking_ref')
    email = request.json.get('email')

    # can not cache because when canceling a booking I have to check to see if the data is been updated to canceled 
    # cache_key = f"booking:{booking_ref}:{email.lower()}"
    # cached_response = cache.get(cache_key)

    # if cached_response:
    #     return cached_response 

    reservation = Pull_GetReservationByID_RQ(username, password, booking_ref)

    response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
    jsonResponse = reservation.get_details(response.text)
    statusCode = int(jsonResponse["Pull_GetReservationByID_RS"]["Status"]["@ID"])
    statusText = jsonResponse["Pull_GetReservationByID_RS"]["Status"]["#text"]



    
    if (statusCode != 0):

        if (statusCode == 28):
            return jsonify({'error': statusText}), 420

        return jsonify({'error': statusText}), 400

    bookingEmail = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["CustomerInfo"]["Email"]
    dateFrom = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("DateFrom")
    dateTo = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("DateTo")
    rentalsUnitedComments = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["Comments"]
    rentalsUnitedCommentsJson = json.loads(rentalsUnitedComments)
    refundable = bool(rentalsUnitedCommentsJson["refundable"])

    # 1 - Confirmed
    # 2 - Canceled
    reservationStatusID = int(jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StatusID"])
    

    date_from_obj = datetime.strptime(dateFrom, "%Y-%m-%d")
    date_to_obj = datetime.strptime(dateTo, "%Y-%m-%d")


    # Calculate if the check-in is more than 14 days away
    today = datetime.today()
    diffDays = (date_from_obj - today).days


    nights = (date_to_obj - date_from_obj).days


    breakdown = []

    # need to figure out the base price but the issue is that if they go to this booking like 2 months from now it will still try 
    # and calculate the price they paid based on the prices json file which might be different best way is database just saying

    basePrice = float(jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("Costs", {}).get("RUPrice"))
    per_night_price = round(basePrice/nights , 2)


    breakdown.append({
        "label": f"£{per_night_price} x {nights} nights",
        "amount": round(basePrice, 2)
    })

    if refundable:
        refundable_rate_fee = Pull_ListPropertyPrices_RQ.calculate_refundable_rate_fee(basePrice)
        breakdown.append({
            "label": "Refundable rate",
            "amount": refundable_rate_fee
        })

    if email.lower() != bookingEmail.lower():
        return jsonify({'error': statusText}), 420

    reservation_data = {
        "reservationStatusID": reservationStatusID,
        "ReservationID": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["ReservationID"],
        "Apartment": apartment_ids.get(int(jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("PropertyID", -1)), "Unknown Apartment"),
        "DateFrom": dateFrom,
        "DateTo": dateTo,
        "ClientPrice": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("Costs", {}).get("ClientPrice"),
        "refundable": refundable,
        "SpecialRequest": rentalsUnitedCommentsJson["specialRequest"],
        "breakdown": breakdown,
        "diffDays": diffDays
    }

    # Add optional fields only if they exist
    if "CustomerInfo" in jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]:
        reservation_data["CustomerInfo"] = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["CustomerInfo"]

    if "GuestDetailsInfo" in jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]:
        reservation_data["GuestDetailsInfo"] = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["GuestDetailsInfo"]

    response_data = {'reservation_data': reservation_data}

    # cache.set(cache_key, response_data, timeout=300)  # Store in cache

    return jsonify(response_data)

@app.route('/get_reviews', methods=['POST'])
def get_reviews():
    cache_key = make_cache_key()  # Generate key based on request data
    cached_response = cache.get(cache_key)

    if cached_response:
        return cached_response  # Return cached response if exists

    try:
        # Read and clean data
        df = pd.read_csv("reviews.csv", keep_default_na=False)
        
        # Convert columns
        numeric_cols = ["Review score", "Staff", "Cleanliness", "Location", 
                       "Facilities", "Comfort", "Value for money"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Handle dates
        df['Review date'] = pd.to_datetime(df['Review date'], errors='coerce')
        df = df.dropna(subset=['Review date'])

        # Get filters from request
        topics = request.json.get("topics", [])
        search_term = request.json.get("search", "").lower().strip()

        # Initialize masks
        topics_mask = pd.Series(False, index=df.index)
        search_mask = pd.Series(False, index=df.index)

        # Build topics mask (OR between topics)
        if topics:
            for topic in topics:
                topic_lower = topic.lower()
                topic_mask = (
                    df['Review title'].str.lower().str.contains(topic_lower, na=False) |
                    df['Positive review'].str.lower().str.contains(topic_lower, na=False)
                )
                topics_mask |= topic_mask

        # Build search mask
        if search_term:
            search_mask = (
                df['Review title'].str.lower().str.contains(search_term, na=False) |
                df['Positive review'].str.lower().str.contains(search_term, na=False)
            )

        # Combine masks with OR logic
        if topics and search_term:
            combined_mask = topics_mask | search_mask
        elif topics:
            combined_mask = topics_mask
        elif search_term:
            combined_mask = search_mask
        else:
            combined_mask = pd.Series(True, index=df.index)  # Show all if no filters

        # Apply the combined filter
        df = df[combined_mask]

        # Sorting implementation
        sort_by = request.json.get("sort_by", "date")
        sort_order = request.json.get("sort_order", "desc")
        
        sort_columns = {
            "date": "Review date",
            "rating": "Review score"
        }
        
        if sort_by in sort_columns:
            sort_column = sort_columns[sort_by]
            df = df.sort_values(
                sort_column, 
                ascending=(sort_order == "asc")
            )

        # Pagination
        page = request.json.get("page", 1)
        limit = request.json.get("limit", 10)
        start = (page - 1) * limit
        end = start + limit

        # Convert to records
        reviews = df.iloc[start:end].to_dict(orient="records")

        response = jsonify({
            "reviews": reviews,
            "page": page,
            "limit": limit,
            "total": len(df),
            "sort_by": sort_by,
            "sort_order": sort_order,
            "search_term": search_term,
            "topics": topics
        })

        cache.set(cache_key, response, timeout=300)  # Store in cache

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))