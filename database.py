import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def create_provisional_booking( *, user_id=None, name, email, phone=None, zip_code=None, country=None, apartment_id, date_from, date_to, nights, adults, children=0, children_ages=None, special_requests=None, refundable=False, client_price=0.0, ru_price=None, payment_intent_id=None):
    """
    Create a provisional booking in the bookings table.
    RU booking reference is left empty until confirmation.
    """

    data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "phone": phone,
        "zip_code": zip_code,
        "country": country,
        "apartment_id": apartment_id,
        "date_from": date_from,
        "date_to": date_to,
        "nights": nights,
        "adults": adults,
        "children": children,
        "children_ages": children_ages or [],
        "special_requests": special_requests,
        "refundable": refundable,
        "client_price": client_price,
        "ru_price": ru_price,
        "ru_booking_reference": None,
        "ru_status": "pending",
        "payment_intent_id": payment_intent_id,
        "payment_status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("bookings").insert(data).execute()
    return response.data


def confirm_booking(booking_id: str, ru_booking_reference: str):
    """
    Confirm a booking by setting RU reference and updating status.
    """
    update_data = {
        "ru_booking_reference": ru_booking_reference,
        "ru_status": "confirmed",
        "updated_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("bookings").update(update_data).eq("id", booking_id).execute()
    return response.data

def payment_captured(booking_id: str, payment_status="confirmed"):
    """
    Confirm a booking by setting RU reference and updating status.
    """
    update_data = {
        "payment_status": payment_status,
        "updated_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("bookings").update(update_data).eq("id", booking_id).execute()
    return response.data



# Provisional booking
# provisional = create_provisional_booking(
#     name="John Doe",
#     user_id="76ae086e-d4c4-4b07-a666-4473e851b682",
#     email="john@example.com",
#     phone="1234567890",
#     zip_code="E1 6AN",
#     country="UK",
#     apartment_id="APT123",
#     date_from="2025-10-01",
#     date_to="2025-10-05",
#     nights=4,
#     adults=2,
#     children=1,
#     children_ages=[6],
#     client_price=500.00,
#     ru_price=450.00,
#     payment_intent_id="pi_123456"
# )
# print("Provisional booking:", provisional)

# Later, after RU confirmation
booking_id = "b132555e-66dd-49ae-a642-7468229581d6"
# confirmed = confirm_booking(booking_id, ru_booking_reference="RU12345ABC")
confirmed = payment_captured(booking_id)
print("Confirmed booking:", confirmed)
