import requests
from datetime import datetime
from add_booking import Push_PutConfirmedReservationMulti_RQ
from get_booking import Pull_GetReservationByID_RQ
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




    # Now add the prices to each apartment and include the overlap logic
    for apartment in properties['available']:
        apartment_prices = prices[str(apartment['id'])]
        if apartment_prices['Prices']:
            apartment['Prices'] = apartment_prices['Prices']  # Add the list of prices for this apartment
        else:
            apartment['Prices'] = 'N/A'  # Default to 'N/A' if no price is found

    return jsonify({'properties': properties})


@app.route('/check_price', methods=['POST'])
def check_price():

    property_id = request.json['property_id']

    # Check Apartment Price
    
    prices = Pull_ListPropertyPrices_RQ.get_all_prices()[str(property_id)]

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

    cancelURL = request.json["url"]
    date_from_obj = datetime(day=date_from["day"], month=date_from["month"], year=date_from["year"])
    date_to_obj = datetime(day=date_to["day"], month=date_to["month"], year=date_to["year"])

     # Check Availability Calendar
    avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
        username, password, property_id=property_id,
        date_from=date_from_obj, 
        date_to=date_to_obj
    )

    response = requests.post(api_endpoint, data=avail_request.serialize_request(), headers={"Content-Type": "application/xml"})
    calendar = avail_request.check_availability_calendar(response.text)
    
    for day in calendar:
        if day["IsBlocked"] == "true":
            return jsonify({'error': 'This apartment is not available for these dates!'}), 420
    
    

    # Calculate the number of nights
    nights = (date_to_obj - date_from_obj).days

    # Get Price
    customerPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=property_id, guests=(adults+children),
        date_from=date_from_obj, 
        date_to=date_to_obj
    )
    if customerPrice == 0:
        return jsonify({'error': 'This apartment is not available for these dates!'}), 420

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
            cancel_url=cancelURL,
            custom_fields=[
                {
                    "key": "special_request",
                    "label": {"type": "custom", "custom": "Special Requests"},
                    "type": "text",
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
                "description": "d",
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
                "capture_method": "manual",
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

    ruPrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(property_id=apartment_id, guests=(adults+children),
        date_from = datetime(day=dateFrom["day"], month=dateFrom["month"], year=dateFrom["year"]),
        date_to= datetime(day=dateTo["day"], month=dateTo["month"], year=dateTo["year"])
    )
    
    booking_info = f"Booking Information:\nAdults: {adults}\nChildren: {children}"
    if children > 0:
        for i, age in enumerate(childrenAges, 1):
            booking_info += f"\nChild {i}: {age} Years Old"
    if special_request != "":
        booking_info += f"\n\nSpecial Request:\n{special_request}"
    booking_info+= f"\n\nStripes Payment ID: {payment_intent_id}"
    booking_info+= f"\n\nCountry: {country}"

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
        commission=0
    )
    response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
    
    jsonResponse = reservation.booking_reference(response.text)
    status = int(jsonResponse["Push_PutConfirmedReservationMulti_RS"]["Status"]["@ID"])
    
    if status !=0:
        payment_intent.cancel()
        error = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["Status"]["#text"]
        redirect_url = (
            f"http://localhost:5173/details?"
            f"name={name}&email={email}&phone_number={phone_number}&"
            f"apartment_name={apartment_name}&price={ruPrice}&"
            f"date_from={date_from}&date_to={date_to}&adults={adults}&children={children}&"
            f"children_ages={','.join(childrenAges)}&nights={nights}&error={error}&errorCode={status}"
        )
        return redirect(redirect_url)

    payment_intent.capture()


    current_meta_data_pi["booking_reference"] = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]
    current_meta_data_pi["name"] = name
    current_meta_data_pi["email"] = email
    current_meta_data_pi["phone_number"] = phone_number
    payment_intent.modify(payment_intent_id,metadata=current_meta_data_pi)
   
    # Include additional data in the redirect URL
    redirect_url = (f"http://localhost:5173/details?ref_number={jsonResponse['Push_PutConfirmedReservationMulti_RS']['ReservationID']}")

    return redirect(redirect_url)

@app.route('/get_booking', methods=['POST'])
def get_booking():
    booking_ref = request.json.get('booking_ref')
    reservation = Pull_GetReservationByID_RQ(username, password, booking_ref)

    response = requests.post(api_endpoint, data=reservation.serialize_request(), headers={"Content-Type": "application/xml"})
    jsonResponse = reservation.get_details(response.text)
    
    reservation_data = {
        "ReservationID": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["ReservationID"],
        "Apartment": apartment_ids.get(int(jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("PropertyID", -1)), "Unknown Apartment"),
        "DateFrom": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("DateFrom"),
        "DateTo": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("DateTo"),
        "ClientPrice": jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["StayInfos"]["StayInfo"].get("Costs", {}).get("ClientPrice")
    }

    # Add optional fields only if they exist
    if "CustomerInfo" in jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]:
        reservation_data["CustomerInfo"] = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["CustomerInfo"]

    if "GuestDetailsInfo" in jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]:
        reservation_data["GuestDetailsInfo"] = jsonResponse["Pull_GetReservationByID_RS"]["Reservation"]["GuestDetailsInfo"]

    return jsonify({'reservation_data': reservation_data})

if __name__ == '__main__':
    app.run()