import requests
from datetime import datetime
from add_booking import Push_PutConfirmedReservationMulti_RQ
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


    props_request = Pull_ListPropertiesBlocks_RQ(
        username, password, location_id=7912,
        date_from=datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"]),
        date_to=datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    )

    response = requests.post(api_endpoint, data=props_request.serialize_request(), headers={"Content-Type": "application/xml"})
    properties = props_request.check_blocked_properties(response.text, apartment_ids)

    # Fetch prices for available apartments
    prices = Pull_ListPropertyPrices_RQ.get_all_prices()

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

    property_id = request.json['property_id']

    # Check Apartment Price

    prices = Pull_ListPropertyPrices_RQ.get_prices_for_property(property_id=property_id)

    return prices

@app.route('/check_calendar', methods=['POST'])
def check_calendar():

    date_from = request.json['date_from']
    date_to = request.json['date_to']
    property_id = request.json['property_id']
    

    # Check Availability Calendar
    avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
        username, password, property_id=property_id,
        date_from=datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"]), 
        date_to=datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    )

    response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})
    calendar = avail_request.check_availability_calendar(response.text)

    return calendar



@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    property_id = request.json['property_id']
    adults = int(request.json['adults'])
    children = int(request.json['children'])
    childrenAges = request.json['childrenAges']
    apartment_number = apartment_ids[property_id].split()[-1]
    image = "https://rosedene.funkypanda.dev/"+str(apartment_number)+"/0.jpg"

     # Check Availability Calendar
    avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
        username, password, property_id=property_id,
        date_from=datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"]), 
        date_to=datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    )

    response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})
    calendar = avail_request.check_availability_calendar(response.text)
    
    for day in calendar:
        if day["IsBlocked"] == "true":
            return jsonify({'error': 'This apartment is not available for these dates!'}), 420
    
    

    # Calculate the number of nights
    date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
    date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])
    nights = (date_to_obj - date_from_obj).days

    # Get Price
    customerPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=property_id, nights=nights, guests=(adults+children))

    displayDate = f'{date_from["day"]}/{date_from["month"]}/{date_from["year"]} - {date_to["day"]}/{date_to["month"]}/{date_to["year"]}'
    description = f"{displayDate} • {adults} Adult{'s' if adults > 1 else ''}"
    if children > 0:
        description += f" • {children} Child{'ren' if children != 1 else ''}"

    

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "gbp",
                        "product_data": {
                            "name": apartment_ids[property_id],
                            "description": description,
                            "images": [image],
                        },
                        "unit_amount_decimal": customerPrice * 100,
                    },
                    "quantity": 1,
                },
            ],
            mode='payment',
            phone_number_collection={"enabled": True},
            success_url="http://127.0.0.1:5000/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=YOUR_DOMAIN + '/cancel.html',
            custom_fields=[
                {
                    "key": "special_request",
                    "label": {"type": "custom", "custom": "Special Requests"},
                    "type": "text",
                    # 'text': {'default_value': "Enter Your Message Here..."},
                    'optional': True,
                }
            ],
            metadata={
                "apartment_id": property_id,
                "apartment_name": apartment_ids[property_id],
                "date_from": f"{date_from['day']}/{date_from['month']}/{date_from['year']}",
                "date_to": f"{date_to['day']}/{date_to['month']}/{date_to['year']}",
                "adults": adults,
                "children": children,
                "children_ages": ",".join(str(e) for e in childrenAges),
                "nights": nights,
                "price": customerPrice
            },
            payment_intent_data={  # Add this section
                "description": f"Booking for {apartment_ids[property_id]} from {date_from['day']}/{date_from['month']}/{date_from['year']} to {date_to['day']}/{date_to['month']}/{date_to['year']} • {adults} Adult{'s' if adults > 1 else ''}" + (f" • {children} Child{'ren' if children != 1 else ''}" if children > 0 else ""),
                "metadata": {
                    "apartment_id": property_id,
                    "apartment_name": apartment_ids[property_id],
                    "date_from": f"{date_from['day']}/{date_from['month']}/{date_from['year']}",
                    "date_to": f"{date_to['day']}/{date_to['month']}/{date_to['year']}",
                    "adults": adults,
                    "children": children,
                    "children_ages": ",".join(str(e) for e in childrenAges),
                    "nights": nights,
                    "price": customerPrice,
                    "name": "",
                    "email": "",
                    "phone_number": "",
                    "booking_reference": ""
                },
            }
        )
    except Exception as e:
        return str(e)

    return jsonify({'url': checkout_session.url})

@app.route('/success', methods=['GET'])
def order_success():
    session_id = request.args.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    payment_intent_id = session.get("payment_intent")
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    current_meta_data_pi = payment_intent.metadata

    charge_intent_id = payment_intent.get("latest_charge")
    charge_intent = stripe.Charge.retrieve(charge_intent_id)

    balance_transaction_id = charge_intent.get("balance_transaction")
    balance_transaction = stripe.BalanceTransaction.retrieve(balance_transaction_id)

    fee = balance_transaction.get("fee")/100


    #  Customer Details
    name = session["customer_details"]["name"]
    email = session["customer_details"]["email"]
    phone_number = session["customer_details"]["phone"]
    postal_code = session["customer_details"]["address"]["postal_code"]
    country = session["customer_details"]["address"]["country"]

    # Special Requestæ
    special_request = session.get("custom_fields", [{}])[0].get("text", {}).get("value", "") or ""

    meta_data = session["metadata"]
    adults = int(meta_data["adults"])
    apartment_id = int(meta_data["apartment_id"])
    apartment_name = meta_data["apartment_name"]
    children = int(meta_data["children"])
    childrenAges = []
    if children > 0:
        childrenAges = meta_data["children_ages"].split(",")
    date_from = meta_data["date_from"]
    date_to = meta_data["date_to"]
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

    ruPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=apartment_id, nights=nights, guests=(adults+children))
    
    booking_info = f"Booking Information:\nAdults: {adults}\nChildren: {children}"
    if children > 0:
        for i, age in enumerate(childrenAges, 1):
            booking_info += f"\nChild {i}: {age} Years Old"
    if special_request != "":
        booking_info += f"\n\nSpecial Request:\n{special_request}"
    booking_info+= f"\n\nStripes Payment ID: {payment_intent_id}"

    # Add Booking to Rentals United
    
    reservation = Push_PutConfirmedReservationMulti_RQ(
        username,
        password,
        property_id=apartment_id,
        date_from = datetime(day=dateFrom["day"], month=dateFrom["month"], year=dateFrom["year"]),
        date_to= datetime(day=dateTo["day"], month=dateTo["month"], year=dateTo["year"]),
        number_of_guests= adults+children,
        client_price=ruPrice,
        ru_price=ruPrice,
        already_paid=ruPrice,
        customer_name=name,
        customer_surname=" ",
        customer_email=email,
        customer_phone=phone_number,
        customer_zip_code=postal_code,
        number_of_adults=adults,
        number_of_children=children,
        children_ages=childrenAges,
        comments=booking_info,
        commission=f"{fee:.2f}"
    )
    response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
    print(response.text)
    booking_reference = reservation.booking_reference(response.text)

    current_meta_data_pi["booking_reference"] = booking_reference
    current_meta_data_pi["name"] = name
    current_meta_data_pi["email"] = email
    current_meta_data_pi["phone_number"] = phone_number
    payment_intent.modify(payment_intent_id,metadata=current_meta_data_pi)
   
    # Include additional data in the redirect URL
    redirect_url = (
        f"http://localhost:5173/?"
        f"name={name}&email={email}&phone_number={phone_number}&"
        f"apartment_name={apartment_name}&amount={ruPrice}&ref_number={booking_reference}&"
        f"check_in={date_from}&check_out={date_to}&adults={adults}&children={children}&"
        f"children_ages={','.join(childrenAges)}&nights={nights}"
    )

    return redirect(redirect_url)

@app.route('/get_booking', methods=['POST'])
def get_booking():
    try:
        payment_intent_id = request.json.get('receipt_id')

        
        # Attempt to retrieve the PaymentIntent
        payment_intent = stripe.PaymentIntent.retrieve(f"pi_{payment_intent_id}", expand=["customer"])
        
        # Extract customer metadata
        return jsonify({'metadata': payment_intent.metadata})

    except stripe.error.InvalidRequestError:
        # If the payment intent does not exist or is invalid
        return jsonify({'error': 'Could not find order', 'code': 'ORDER_NOT_FOUND'}), 404

    except Exception as e:
        # Handle any other unexpected errors
        return jsonify({'error': 'Something went wrong', 'code': 'SERVER_ERROR', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run()