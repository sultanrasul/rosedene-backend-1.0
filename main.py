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

        if not props_request or "available" not in props_request:
            return jsonify({"error": "Apartment is blocked for selected dates"}), 400
            
        # Now add the prices to each apartment and include the overlap logic
        for apartment in properties['available']:
            apartment_prices = prices[str(apartment['id'])]
            if apartment_prices['Prices']:
                apartment['Prices'] = apartment_prices['Prices']  # Add the list of prices for this apartment
            else:
                apartment['Prices'] = 'N/A'  # Default to 'N/A' if no price is found

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
# @cache.memoize(timeout=300) # this does not work because if someone was to go to apatment 1 check the price then went to apartment 2 they would still get the price for apartment 1
def verify_price():
    property_id = request.json['property_id']
    refundable = request.json['refundable']
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    adults = int(request.json['adults'])
    children = int(request.json['children'])


    date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
    date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])

    nights = (date_to_obj - date_from_obj).days

    basePrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=property_id, guests=(adults+children),
        date_from=date_from_obj, 
        date_to=date_to_obj,
    )

    clientPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(basePrice=basePrice, refundable=refundable)

    per_night_price = round(basePrice/nights , 2)

    breakdown = []


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

    return jsonify({
        "total": clientPrice,
        "breakdown": breakdown
    })

# This gives back the specific apartment availability for the next 2 years
@app.route('/check_calendar', methods=['POST'])
def check_calendar():

    property_id = request.json['property_id']
    date_from = datetime.today()
    date_to = date_from + relativedelta(years=2)


    # Check Availability Calendar
    avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
        username, password, property_id=property_id,
        date_from=date_from, 
        date_to=date_to
    )

    response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})
    calendar = avail_request.check_availability_calendar(response.text)

    return calendar

@app.route('/create-checkout', methods=['POST'])
def create_checkout():
    try:
        data = request.get_json()
        required_fields = ["date_from", "date_to", "property_id", "adults", "children", "childrenAges", "refundable", "name", "phone", "email", "special_requests"]


        # 1. Validate all fields
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # 2. Parse input values

        # Booking Information
        property_id = int(data['property_id'])
        adults = int(data['adults'])
        children = int(data['children'])
        childrenAges = data['childrenAges']
        refundable = bool(data['refundable'])
        total_guests = adults + children
        

        # Guest Information
        name = data['name'].strip()
        phone = data['phone'].strip()
        email = data['email'].strip()
        specialRequests = data['special_requests']


        apartment_number = apartment_ids[property_id].split()[-1]

        # cancelURL = request.json["url"] not sure if I still send that from the frontend
        try:
            date_from = data['date_from']
            date_to = data['date_to']
            date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
            date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
        except Exception:
            return jsonify({"error": "Invalid date format"}), 400
        
        nights = (date_to_obj - date_from_obj).days
        if nights <= 0:
            return jsonify({"error": "Invalid date range"}), 400

        # 3. Enforce max guest limit
        apartment_number = int(apartment_ids[property_id].split()[-1])  # e.g. "Apartment 5" → 5
        max_allowed = max_guests.get(apartment_number)
        if max_allowed and total_guests > max_allowed:
            return jsonify({"error": f"Max guests allowed: {max_allowed}"}), 400

        # Check Availability Calendar
        avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
            username, password, property_id=property_id,
            date_from=date_from_obj, 
            date_to=date_to_obj
        )
        if children+adults > max_guests[int(apartment_number)]:
            return jsonify({'error': f'Max Guests allowed for this apartment is {max_guests[int(apartment_number)]}'}), 420

        response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})
        calendar = avail_request.check_availability_calendar(response.text)
        
        for day in calendar:
            if day["IsBlocked"] == "true":
                return jsonify({"error": "Apartment is not available for selected dates"}), 409

        # Get Price
        basePrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=property_id, guests=total_guests,
            date_from=date_from_obj, 
            date_to=date_to_obj,
        )
        customerPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(basePrice=basePrice, refundable=refundable)


        if customerPrice == 0:
            return jsonify({'error': 'This apartment is not available for these dates!'}), 500

        displayDate = f'{date_from["day"]}/{date_from["month"]}/{date_from["year"]} - {date_to["day"]}/{date_to["month"]}/{date_to["year"]}'
        description = f"{displayDate} • {adults} Adult{'s' if adults > 1 else ''}"
        if children > 0:
            description += f" • {children} Child{'ren' if children != 1 else ''}"
        

        payment_intent = stripe.PaymentIntent.create(
            amount=int(customerPrice * 100),
                # Amount in pence
            currency='gbp',
            payment_method_types=['card'],

            # Leave out paypal and revoult for now because I need to implement the redirects
            # automatic_payment_methods={
            #     'enabled': True,
            # },
            metadata={
                "apartment_id": property_id,
                "apartment_name": apartment_ids[property_id],
                "date_from": f"{date_from['day']}/{date_from['month']}/{date_from['year']}",
                "date_to": f"{date_to['day']}/{date_to['month']}/{date_to['year']}",
                "adults": adults,
                "children": children,
                "children_ages": ",".join(str(e) for e in childrenAges),
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
            capture_method='manual'  # Keep if you need manual capture
        )

        logging.info({
            "severity": "INFO",
            "message": "Create Checkout Request",
            "payment_intent_id": payment_intent.id,
            "property_id": property_id,
            "guests": adults + children,
            "refundable": refundable,
            "date_from": str(date_from),
            "date_to": str(date_to),
            "client_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
        })

        return jsonify({
                'clientSecret': payment_intent.client_secret,
                'amount': customerPrice  # Optional: Send amount for display
            })
    
    except Exception as e:
        logging.exception("⚠️ Failed to create checkout")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/update-guest-info', methods=['POST'])
def update_guest_info():
    data = request.json
    client_secret = data.get('client_secret')

    # Validate input
    if not client_secret:
        return jsonify({"error": "Missing client_secret"}), 400

    # Extract metadata fields
    name = data.get('name', '')
    phone = data.get('phone', '')
    email = data.get('email', '')
    special_requests = data.get('special_requests', '')
    payment_intent_id = client_secret.split("_secret")[0]

    try:
        # Update metadata
        stripe.PaymentIntent.modify(
            payment_intent_id,
            metadata={
                "name": name,
                "phone_number": phone,
                "email": email,
                "special_requests": special_requests
            }
        )
        
        logging.info({
            "severity": "INFO",
            "message": "Updated Guest Information At Checkout",
            "payment_intent_id": payment_intent_id,
            "client_ip": request.headers.get('X-Forwarded-For', request.remote_addr)
        })

        return jsonify({"message": "Guest info updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    try:
        data = request.json
        booking_ref = data.get('booking_ref')
        email = data.get('email')
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        if not booking_ref or not email:
            logging.warning({
                "message": "Missing booking_ref or email",
                "booking_ref": booking_ref,
                "email": email,
                "ip": user_ip,
                "severity": "WARNING"
            })
            return jsonify({'error': 'Missing booking_ref or email'}), 400

        logging.info({
            "message": "Cancellation attempt received",
            "booking_ref": booking_ref,
            "email": email,
            "ip": user_ip,
            "severity": "INFO"
        })

        # Get booking details
        reservation = Pull_GetReservationByID_RQ(username, password, booking_ref)
        response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
        booking_data = reservation.get_details(response.text)

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

        # Extract data...
        reservation_data = booking_data["Pull_GetReservationByID_RS"]["Reservation"]
        reservationID = reservation_data["ReservationID"]
        rentalsUnitedCommentsJson = json.loads(reservation_data["Comments"])
        bookingEmail = reservation_data["CustomerInfo"]["Email"]

        # Customer Info
        customer_info = reservation_data["CustomerInfo"]
        bookingEmail = customer_info["Email"]
        name = customer_info["Name"]
        phone = customer_info["Phone"]

        # Booking Info
        booking_info = reservation_data["StayInfos"]["StayInfo"]
        dateFrom = booking_info.get("DateFrom")
        dateTo = booking_info.get("DateTo")

        date_from_obj = datetime.strptime(dateFrom, "%Y-%m-%d")
        date_to_obj = datetime.strptime(dateTo, "%Y-%m-%d")
        nights = (date_to_obj - date_from_obj).days

        apartmentID = int(booking_info.get("PropertyID"))

        # Guest Info
        guest_info = reservation_data["GuestDetailsInfo"]

        adults = int(guest_info["NumberOfAdults"])
        children = int(guest_info["NumberOfChildren"])

        # Default to an empty list
        childrenAges = []

        if children > 0:
            age_data = guest_info.get("ChildrenAges", {}).get("Age", [])
            
            if isinstance(age_data, list):
                childrenAges = age_data
            elif isinstance(age_data, str):
                childrenAges = [age_data]
        



        if email.lower() != bookingEmail.lower():
            return jsonify({'error': 'Email does not match booking'}), 420

        refundable = rentalsUnitedCommentsJson.get("refundable", False)
        paymentIntentId = rentalsUnitedCommentsJson.get("paymentIntentId")
        specialRequest = rentalsUnitedCommentsJson.get("specialRequest")

        if email.lower() != bookingEmail.lower():
            logging.warning({
                "message": "Email mismatch during cancellation",
                "submitted_email": email,
                "booking_email": bookingEmail,
                "booking_ref": booking_ref,
                "severity": "WARNING"
            })
            return jsonify({'error': 'Email does not match booking'}), 420

        refundable = rentalsUnitedCommentsJson.get("refundable", False)
        paymentIntentId = rentalsUnitedCommentsJson.get("paymentIntentId")

        # Step 1: Cancel in Rentals United
        try:
            cancel = Push_CancelReservation_RQ(username, password, booking_ref, cancel_type_id=2)
            cancel_response = requests.post(api_endpoint, data=cancel.serialize_request(), headers={"Content-Type": "application/xml"})
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

        # Step 2: Refund via Stripe
        refund_successful = False
        if refundable:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(paymentIntentId, expand=["charges"])
                charge_id = payment_intent.latest_charge

                if not charge_id:
                    raise Exception("No charge found for PaymentIntent")

                refund = stripe.Refund.create(
                    charge=charge_id,
                    reason='requested_by_customer'
                )
                refund_successful = refund.status == "succeeded"
                if not refund_successful:
                    raise Exception("Refund status not succeeded")

                logging.info({
                    "message": "Stripe refund successful",
                    "payment_intent_id": paymentIntentId,
                    "charge_id": charge_id,
                    "refund_status": refund.status,
                    "severity": "INFO"
                })

            except Exception as e:
                logging.exception(f"❌ Refund failed for payment intent {paymentIntentId}")
                return jsonify({'error': f'Refund failed: {str(e)} — booking not cancelled'}), 500

        # Step 3: Send Cancelation Email

        ruPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=apartmentID, guests=(adults+children),
            date_from = date_from_obj,
            date_to= date_to_obj,
        )

        clientPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(basePrice=ruPrice, refundable=refundable)

        breakdown = []
        
        per_night_price = round(ruPrice/nights , 2)

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

            # Add spacer row except after the last item
            if index < len(breakdown) - 1:
                breakdown_html_rows += """
                <tr>
                    <td colspan="2" height="15"></td>
                </tr>
                """

        try:
            email_sender = create_email(
                name=name,
                breakdown_html_rows=breakdown_html_rows,
                clientPrice=clientPrice,
                booking_reference=reservationID,
                date_from=f"{date_from_obj.day} {date_from_obj.strftime('%b')} {date_from_obj.year}",
                date_to=f"{date_to_obj.day} {date_to_obj.strftime('%b')} {date_to_obj.year}",
                apartmentName=apartment_ids[apartmentID],
                phone=phone,
                adults=adults,
                children=children,
                childrenAges=childrenAges,
                nights=nights,
                refundable=refundable,
                email=email,
                specialRequests=specialRequest,
                cancel=True
            )
            email_sender.send_email(os.getenv('email'))

            logging.info({
                "message": "Cancelation email sent",
                "booking_ref": booking_ref,
                "email": email,
                "severity": "INFO"
            })

        except Exception as e:
            logging.exception(f"❌ Failed to send cancellation email for {booking_ref}")

        return jsonify({'message': 'Booking cancelled and refunded successfully'})

    except Exception as e:
        logging.exception("🔥 Uncaught error in cancel_booking route")
        return jsonify({'error': 'Something went wrong processing the cancel request'}), 500



@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, stripe_webhook_key)
    except ValueError as e:
        logging.exception("⚠️ Invalid payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        logging.exception("⚠️ Invalid signature")
        return jsonify({"error": "Invalid signature"}), 400

    if event['type'] != 'charge.succeeded':
        logging.info({
            "message": "Ignored Stripe webhook event",
            "event_type": event['type'],
        })
        return jsonify({"message": "Event ignored"}), 200

    try:
        # Handle the event
        charge_obj = event['data']['object']
        payment_intent_id = charge_obj["payment_intent"]
        # payment_intent_object = stripe.PaymentIntent.retrieve(payment_intent_id)
        billing_details = charge_obj['billing_details']
        name = billing_details["name"]
        phone = billing_details["phone"]
        email = billing_details["email"]
        country = billing_details["address"]["country"]
        postal_code = billing_details["address"]["postal_code"]

        meta_data = charge_obj.metadata

        required_fields = ["adults", "children", "apartment_id", "refundable", "date_from", "date_to", "nights"]
        for field in required_fields:
            if field not in meta_data:
                raise ValueError(f"Missing required metadata field: {field}")

        adults = int(meta_data["adults"])
        apartment_id = int(meta_data["apartment_id"])
        refundable = meta_data["refundable"].lower() == "true"
        children = int(meta_data["children"])
        childrenAges = []
        if children > 0:
            childrenAges = meta_data["children_ages"].split(",")
        date_from = meta_data["date_from"]
        date_to = meta_data["date_to"]
        date_from_obj = datetime.strptime(date_from, "%d/%m/%Y")
        date_to_obj = datetime.strptime(date_to, "%d/%m/%Y")
        special_requests = meta_data.get("special_requests", "")
        nights = int(meta_data["nights"])


        dateFrom = {
            "day": int(date_from.split("/")[0]),
            "month": int(date_from.split("/")[1]),
            "year": int(date_from.split("/")[2])
        }
        dateTo = {
            "day": int(date_to.split("/")[0]),
            "month": int(date_to.split("/")[1]),
            "year": int(date_to.split("/")[2])
        }

        ruPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=apartment_id, guests=(adults+children),
            date_from = datetime(day=dateFrom["day"], month=dateFrom["month"], year=dateFrom["year"]),
            date_to= datetime(day=dateTo["day"], month=dateTo["month"], year=dateTo["year"]),
        )

        clientPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(basePrice=ruPrice, refundable=refundable)

        booking_data = {
            "adults": adults,
            "children": children,
            "childrenAges": childrenAges if children > 0 else [],
            "specialRequest": special_requests,
            "refundable": refundable,
            "paymentIntentId": payment_intent_id,
            "country": country
        }

        booking_info = json.dumps(booking_data, indent=2)  # optional `indent` for human-readability


        # Add Booking to Rentals United
        reservation = Push_PutConfirmedReservationMulti_RQ(
            username,
            password,
            property_id=apartment_id,
            date_from = datetime(day=dateFrom["day"], month=dateFrom["month"], year=dateFrom["year"]),
            date_to= datetime(day=dateTo["day"], month=dateTo["month"], year=dateTo["year"]),
            number_of_guests= adults+children,
            client_price=clientPrice,
            ru_price=ruPrice,
            already_paid=clientPrice,
            customer_name=name,
            customer_surname=" ",
            customer_email=email,
            customer_phone=phone,
            customer_zip_code=postal_code,
            number_of_adults=adults,
            number_of_children=children,
            children_ages=childrenAges,
            comments=booking_info,
            commission=0
        )
        response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
        jsonResponse = reservation.booking_reference(response.text)

        status_code = int(jsonResponse["Push_PutConfirmedReservationMulti_RS"]["Status"]["@ID"])
        status_text = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["Status"]["#text"]

        if status_code != 0:
            # Abort: cancel payment and record error
            stripe.PaymentIntent.modify(payment_intent_id, metadata={"error_code": status_code, "error_text": status_text})
            stripe.PaymentIntent.cancel(payment_intent_id, cancellation_reason="abandoned")

            logging.error(f"Booking failed with RU error: {status_text}")

            return jsonify({"error": status_text}), 409
            


        booking_reference = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]


        stripe.PaymentIntent.modify(payment_intent_id,metadata={"booking_reference": booking_reference})
        stripe.PaymentIntent.capture(payment_intent_id)

        logging.info({
            "message": "✅ Booking confirmed",
            "booking_reference": booking_reference,
            "payment_intent_id": payment_intent_id 
        })


        # Breaking down the breakdown of what they paid for 

        breakdown = []

        # need to figure out the base price but the issue is that if they go to this booking like 2 months from now it will still try 
        # and calculate the price they paid based on the prices json file which might be different best way is database just saying
        per_night_price = round(ruPrice/nights , 2)

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

            # Add spacer row except after the last item
            if index < len(breakdown) - 1:
                breakdown_html_rows += """
                <tr>
                    <td colspan="2" height="15"></td>
                </tr>
                """

        ###### SEND BOOKING CONFIRMATION ######

        email_sender = create_email(
            name=name,
            breakdown_html_rows=breakdown_html_rows,
            clientPrice=clientPrice,
            booking_reference=booking_reference,
            date_from=f"{date_from_obj.day} {date_from_obj.strftime('%b')} {date_from_obj.year}",
            date_to=f"{date_to_obj.day} {date_to_obj.strftime('%b')} {date_to_obj.year}",
            apartmentName=apartment_ids[apartment_id],
            phone=phone,
            adults=adults,
            children=children,
            childrenAges=childrenAges,
            nights=nights,
            refundable=refundable,
            email=email,
            specialRequests=special_requests,
            cancel=False
        )
        try:
            email_sender.send_email(os.getenv('email'))
            logging.info({
                "message": "📧 Booking email sent",
                "booking_reference": booking_reference
            })
        except Exception as email_error:
            logging.exception(f"❌ Failed to send booking email for reference {booking_reference}")

        ###### SEND BOOKING CONFIRMATION ######


        return jsonify({"message": "Booking completed", "reference": booking_reference}), 200
    
    except Exception as e:
        logging.exception("🔥 Unexpected error in webhook")
        return jsonify({"error": "Internal error during webhook processing"}), 500

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