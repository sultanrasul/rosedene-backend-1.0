import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from add_booking import Push_PutConfirmedReservationMulti_RQ
from get_booking import Pull_GetReservationByID_RQ
from location_check import Pull_ListPropertiesBlocks_RQ
from property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from property_price import Pull_ListPropertyPrices_RQ
from flask import Flask, request, jsonify, redirect
import stripe
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

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

FRONTEND_URL = 'http://localhost:5173'
BACKEND_URL =  'http://127.0.0.1:5000'

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

    property_id = request.json['property_id']
    date_from = datetime.today()
    date_to = date_from + relativedelta(years=3)


    # Check Availability Calendar
    avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
        username, password, property_id=property_id,
        date_from=date_from, 
        date_to=date_to
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
            success_url=BACKEND_URL+"/success?session_id={CHECKOUT_SESSION_ID}",
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
            f"{FRONTEND_URL}/details?"
            f"name={name}&email={email}&phone_number={phone_number}&"
            f"apartment_name={apartment_name}&price={ruPrice}&"
            f"date_from={date_from}&date_to={date_to}&adults={adults}&children={children}&"
            f"children_ages={','.join(childrenAges)}&nights={nights}&error={error}&errorCode={status}"
        )
        return redirect(redirect_url)

    payment_intent.capture()

    ###### SEND BOOKING CONFIRMATION ######

    message = Mail(
    from_email='booking@rosedenedirect.com',
    to_emails='sultanrasul5@gmail.com',
    subject=f'Confirmation of your reservation: Rosedene Highland House No.{jsonResponse["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]}',
    html_content=f'''
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{
            font-family: "Calibri", sans-serif;
        }}
        /* Reset styles for email clients */
        .main-table {{ width: 100% !important; max-width: 600px !important; margin: 0 auto !important; }}
        img {{ border: 0; line-height: 100%; max-width: 100% !important; }}
        .mobile-stack {{ display: block !important; width: 100% !important; }}
        .separator {{ border-left: 1px solid #cccccc; height: 40px; }}
        .data-row {{ padding: 12px 0; border-top: 1px solid #e2e8f0; }}
        
        @media screen and (max-width: 600px) {{
            .main-table, .mobile-stack {{ width: 100% !important; }}
            td.mobile-stack {{ display: block !important; width: 100% !important; }}
            .desktop-hide {{ display: none !important; }}
            .mobile-center {{ text-align: center !important; }}
            .mobile-pad {{ padding: 10px !important; }}
            .mobile-text {{ font-size: 14px !important; }}
            .mobile-header {{ font-size: 20px !important; }}
            img {{ height: auto !important; max-height: 300px !important; }}
        }}
    </style>
    </head>
    <body style="margin:0; padding:20px 0; background:#f5f5f5;">

    <!-- Wrapper Table -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table class="main-table" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
                    <!-- Email Details Section -->
                    <tr>
                        <td style="padding:10px; text-align:center;">
                            <p style="color:#2d3748; font-size:12px; margin:8px 0 30px;text-align:center;">
                                IMPORTANT: This confirmation email has been generated automatically, so please do not reply to this address. To view or cancel your reservation, please go to the "Find Details" section of our website and quote the confirmation or reservation number shown in this email.
                            </p>
                            <img src="https://rosedenedirect.com/logo.png" alt="Rosedene Logo" style="width:90%; max-width:200px; margin:0 auto 30px; display:block;">
                            
                            <!-- Email Content -->
                            <table width="100%" style="border:1px solid #e2e8f0; border-radius:12px; background:#ffffff; padding:20px; text-align:left;margin-bottom:90px;">
                                <tr>
                                    <td>
                                        <p>
                                            Dear, {name}
                                        </p>
                                        <p>
                                            Thank you for choosing 
                                            <span style="color:#C09A5B;font-weight:bold;">Rosedene Highland House</span>
                                            for your next stay in 
                                            <span style="color:#C09A5B;font-weight:bold;">Inverness</span>.
                                        </p>
                                        <p>
                                            Please see below for details of your reservation.
                                        </p>
                                        <p>
                                            We hope you enjoy your stay!
                                        </p>
                                        <p>
                                            Kind regards,<br>
                                            ALL – Rosedene Highland House Customer Service
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Green Checkmark Section -->
                    <tr>
                        <td style="padding:10px; text-align:center;">
                            <table width="100%" style="margin:-0px auto 0;">
                                <tr>
                                    <td align="center">
                                        <div style="width:80px; height:80px; background:#ffffff; border-radius:50%;">
                                            <img src="https://cdn-icons-png.flaticon.com/512/5610/5610944.png" alt="Payment Successful" style="width:100%; height:auto; display:block;">
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Booking Details Section -->
                    <tr>
                        <td style="padding:10px; border-radius:12px;">
                            <table width="100%">
                                <tr>
                                    <td style="text-align:center; padding-bottom:20px;">
                                        <h1 style="color:#C09A5B; font-size:32px; margin:0;padding-top:0px;">
                                            Payment Successful!
                                        </h1>
                                        <p style="color:#666666; font-size:16px; margin:8px 0 0;">
                                            Your reservation is confirmed
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Details Card -->
                            <table width="100%" style="background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0; padding:20px;">
                                <!-- Total Amount -->
                                <tr>
                                    <td style="padding-bottom:15px;">
                                        <table width="100%">
                                            <tr>
                                                <td style="color:#64748b; font-weight:500;">Total Amount</td>
                                                <td style="text-align:right; color:#1e293b; font-size:24px; font-weight:700;">£{ruPrice}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- Reference Number -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="color:#64748b;">Reference Number</td>
                                            <td style="text-align:right; color:#1e293b;">{jsonResponse["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]}</td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Apartment -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="color:#64748b;">Apartment</td>
                                            <td style="text-align:right; color:#1e293b;">{apartment_ids[apartment_id]}</td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Guest Info -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="color:#64748b;">Guest Name</td>
                                            <td style="text-align:right; color:#1e293b;">{name}</td>
                                        </tr>
                                        <tr><td colspan="2" style="padding-top:8px;"></td></tr>
                                        <tr>
                                            <td style="color:#64748b;">Email</td>
                                            <td style="text-align:right; color:#1e293b;">{email}</td>
                                        </tr>
                                        <tr><td colspan="2" style="padding-top:8px;"></td></tr>
                                        <tr>
                                            <td style="color:#64748b;">Phone</td>
                                            <td style="text-align:right; color:#1e293b;">{phone_number}</td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Dates -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="width:50%;">
                                                <div style="color:#64748b;">Check-in</div>
                                                <div style="color:#1e293b; font-weight:500;">{date_from}</div>
                                            </td>
                                            <td style="width:0%; text-align:center;">
                                                <div class="separator"></div>
                                            </td>
                                            <td style="width:50%;text-align: right;">
                                                <div style="color:#64748b;">Check-out</div>
                                                <div style="color:#1e293b; font-weight:500;">{date_to}</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Guest Details -->
                                <tr><td class="data-row">
                                        <table width="100%">
                                            <tr>
                                                <td style="width:33%; text-align: left;">
                                                    <div style="color:#64748b;">Adults</div>
                                                    <div style="color:#1e293b; font-weight:500;">{adults}</div>
                                                </td>
                                                <td style="width:33%; text-align: center;">
                                                    <div style="color:#64748b;">Children</div>
                                                    <div style="color:#1e293b; font-weight:500;">{children}</div>
                                                </td>
                                                <td style="width:33%; text-align: right;">
                                                    <div style="color:#64748b;">Nights</div>
                                                    <div style="color:#1e293b; font-weight:500;">{nights}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td></tr>
                                
                                <!-- Children Ages (Conditional) -->
                                {
                                    f"""
                                        <tr>
                                            <td>
                                                <table width="100%">
                                                    <tr>
                                                        <td style="color:#64748b;">Children Ages</td>
                                                        <td style="text-align:right; color:#1e293b;">{','.join(childrenAges)}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    """ if children != 0 else ""
                                }
                                    
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    </body>
    </html>
    ''')
    
    try:
        sg = SendGridAPIClient(os.getenv('email'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

    ###### SEND BOOKING CONFIRMATION ######


    current_meta_data_pi["booking_reference"] = jsonResponse["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]
    current_meta_data_pi["name"] = name
    current_meta_data_pi["email"] = email
    current_meta_data_pi["phone_number"] = phone_number
    payment_intent.modify(payment_intent_id,metadata=current_meta_data_pi)
   
    # Include additional data in the redirect URL
    redirect_url = (f"{FRONTEND_URL}/details?ref_number={jsonResponse['Push_PutConfirmedReservationMulti_RS']['ReservationID']}")

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
    # app.run(host="192.168.178.63",port=5000)
    app.run(port=5000)