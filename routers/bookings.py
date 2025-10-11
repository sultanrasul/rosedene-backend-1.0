from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from typing import Optional
from services.integrations.supabase_service import SupabaseService  # adjust import to your path

router = APIRouter(prefix="/bookings", tags=["Bookings"])
supabase_service = SupabaseService()


@router.get("/{booking_id}")
async def get_guest_booking(
    request: Request,
    booking_id: str,
    token: str = Query(description="Guest access token"),
):
    """
    Retrieve booking details.
    - If a logged-in user, validate via Supabase JWT.
    - If a guest, validate via token hash.
    """
    try:
        booking = await supabase_service.get_guest_booking_details(
            request=request,
            booking_id=booking_id,
            token=token,
        )
        return booking
    except HTTPException as e:
        # Let HTTPExceptions pass through as-is
        raise e
    except Exception as e:
        print("❌ Unexpected error in get_booking_details:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving booking details."
        )
