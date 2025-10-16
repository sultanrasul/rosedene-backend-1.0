import logging
import hashlib
from datetime import datetime
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from supabase import create_client, Client
from config import settings
from schemas.payments import DateModel, CreateCheckoutRequest
from schemas.booking import Booking
from utils.exceptions import *

# Rentals United integrations
from services.integrations.rentals_united.add_booking import Push_PutConfirmedReservationMulti_RQ
from services.integrations.rentals_united.cancel_booking import Push_CancelReservation_RQ
from services.integrations.rentals_united.get_booking import Pull_GetReservationByID_RQ

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY
        self.supabase_jwt = settings.SUPABASE_JWT
        self.supabase: Client | None = None

        # ✅ Initialize only if valid credentials exist
        if (
            self.supabase_url
            and self.supabase_key
            and self.supabase_url.startswith("http")
        ):
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabase client initialized.")
            except Exception as e:
                print(f"⚠️ Failed to initialize Supabase client: {e}")
        else:
            print("⚠️ Supabase credentials not provided — running in mock/no-database mode.")
            
    async def create_provisional_booking(
        self,
        booking_data: CreateCheckoutRequest,
        base_price: float,
        client_price: float
    ) -> str:
        """Create booking record in supabase before confirming in rentals united"""

        data = booking_data.dict()
        # 🔑 Convert DateModel -> date string YYYY-MM-DD (no time)
        if isinstance(booking_data.date_from, DateModel):
            date_from_obj = booking_data.date_from.to_datetime().date()
            data["date_from"] = date_from_obj.isoformat()
        if isinstance(booking_data.date_to, DateModel):
            date_to_obj = booking_data.date_to.to_datetime().date()
            data["date_to"] = date_to_obj.isoformat()

        nights = (date_to_obj - date_from_obj).days

        data.update({
            "ru_price": base_price,
            "client_price": client_price,
            "ru_booking_reference": None,
            "ru_status": "pending",
            "payment_status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "nights": nights
        })

        response = self.supabase.table("bookings").insert(data).execute()
        booking_id = response.data[0]["id"]

        print("✅ Provisional booking created:", booking_id)
        return booking_id

    async def get_booking_uuid_data(self, booking_id: str) -> Booking:
        response = self.supabase.table("bookings").select("*").eq("id", booking_id).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])  # ✅ make it a Pydantic model
        return None
    
    async def get_booking_ru(self, booking_id: str) -> Booking:
        response = self.supabase.table("bookings").select("*").eq("ru_booking_reference", booking_id).execute()

        if response.data and len(response.data) > 0:
            return Booking(**response.data[0])  # ✅ make it a Pydantic model
        return None

    async def update_booking(self, booking_id: str, **updates):
        """Update any fields in a booking row by booking_id. Pass only the fields you want to change."""
        if not updates:
            raise ValueError("No updates provided")

        response = self.supabase.table("bookings").update(updates).eq("id", booking_id).execute()

        if not response.data:
            print(f"⚠️ No booking found with id {booking_id}")
            return None

        print(f"✅ Booking {booking_id} updated:", updates)

        return response.data[0]

    async def get_guest_booking_details(
        self,
        request: Request,
        booking_id: str,
        token: str,
    ) -> Dict[str, Any]:
        """
        Retrieve booking details.
        - If a valid Bearer token is present, verify user via Supabase Auth API.
        - If no user, verify guest via token hash.
        """
        # ✅ 2. Fetch booking from Supabase
        response = self.supabase.table("bookings").select("*").eq("id", booking_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        booking = response.data[0]
        user_id = booking.get("user_id")

        # ✅ 3. Authorization logic
        if user_id:
            # Logged-in booking — must match
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this booking"
            )
        else:
            # Guest booking — must have token
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing token for guest booking"
                )
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if booking.get("secret_token_hash") != token_hash:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid guest token"
                )

        # ✅ 4. Return booking + user data
        return booking 

    async def verify_user_from_request(self, request: Request):
        """
        Verifies the user making the request using the Supabase JWT in Authorization header.
        Returns the Supabase user object if valid, otherwise raises an HTTPException.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]

        try:
            response = self.supabase.auth.get_user(jwt=token)
            user = response.user
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Auth verification failed: {str(e)}")
        