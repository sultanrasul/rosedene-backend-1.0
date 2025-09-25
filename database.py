import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def create_provisional_booking( *, user_id=None, name, email, phone=None, zip_code=None, country=None, apartment_id, date_from, date_to, nights, adults, children=0, children_ages=None, special_requests=None, refundable=False, client_price=0.0, ru_price=None, payment_intent_id=None, client_secret=None):
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
        "client_secret": client_secret,
        "payment_status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("bookings").insert(data).execute()

    booking_id = response.data[0]["id"]
    print("✅ Provisional booking created:", booking_id)

    return booking_id

def update_booking(booking_id: str, **updates):
    """
    Update any fields in a booking row by booking_id.
    Pass only the fields you want to change.
    Example:
        update_booking("1234-uuid", name="New Name", payment_status="failed")
    """
    if not updates:
        raise ValueError("No updates provided")

    # Always refresh updated_at
    updates["updated_at"] = datetime.utcnow().isoformat()

    response = supabase.table("bookings").update(updates).eq("id", booking_id).execute()

    if not response.data:
        print(f"⚠️ No booking found with id {booking_id}")
        return None

    print(f"✅ Booking {booking_id} updated:", updates)
    return response.data[0]


def confirm_booking(booking_id: str, ru_booking_reference: str, status = "confirmed"):
    """
    Confirm a booking by setting RU reference and updating status.
    """
    update_data = {
        "ru_booking_reference": ru_booking_reference,
        "ru_status": status,
        "updated_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("bookings").update(update_data).eq("id", booking_id).execute()
    return response.data

def cancel_booking_by_ru_reference(ru_booking_reference: str, status="canceled"):
    """
    Cancel a booking by RU booking reference instead of internal UUID.
    """
    update_data = {
        "ru_status": status,
        "updated_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("bookings").update(update_data).eq("ru_booking_reference", ru_booking_reference).execute()

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
