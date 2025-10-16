from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, status, Body
from typing import Any, Dict, Optional
from services.integrations.supabase_service import SupabaseService

router = APIRouter(prefix="/bookings", tags=["Bookings"])
supabase_service = SupabaseService()


@router.post("/get-booking")
async def get_booking(
    request: Request,
    booking_id: str = Body(..., embed=True),
    token: Optional[str] = Body(None, embed=True)
) -> Dict[str, Any]:
    """
    Retrieve booking details:
    - Logged-in user: validated via Supabase JWT.
    - Guest user: validated via guest token.
    """
    try:
        booking = None

        if token:
            # 🎟 Guest user flow
            print("🎟 Guest booking request")
            booking = await supabase_service.get_guest_booking_details(
                request=request,
                booking_id=booking_id,
                token=token,
            )
        else:
            # 🔑 Authenticated user flow
            print("🔑 Authenticated user request")
            user = await supabase_service.verify_user_from_request(request)
            booking = await supabase_service.get_booking_uuid_data(booking_id=booking_id)

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        return booking

    except HTTPException:
        raise
    except Exception as e:
        print("❌ Unexpected error in get_booking:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving booking details."
        )

# Get booking with checkin date, last name and booking confirmation
@router.post("/get-booking-check-in")
async def get_booking(
        request: Request,
        booking_id: str = Body(..., embed=True),
        last_name: str = Body(..., embed=True),
        checkin_date: datetime = Body(..., embed=True),
    ) -> Dict[str, Any]:
    
    booking = await supabase_service.get_booking_ru(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Match surname and date
    if booking.last_name.strip().lower() != last_name.lower():
        raise HTTPException(status_code=401, detail="Surname does not match")

    if booking.date_from.date() != checkin_date.date():
        raise HTTPException(status_code=401, detail="Check-in date does not match")

    # ✅ Return only safe, public info
    return {
        "reference": booking.ru_booking_reference,
        "first_name": booking.first_name,
        "last_name": booking.last_name,
        "apartment_id": booking.apartment_id,
        "date_from": booking.date_from,
        "date_to": booking.date_to,
        "nights": booking.nights,
        "adults": booking.adults,
        "children": booking.children,
        "ru_status": booking.ru_status,
        "country": booking.country,
        "zip_code": booking.zip_code,
    }
