from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from dateutil.relativedelta import relativedelta
from services.integrations.rentals_united_service import RentalsUnitedService
from schemas.property import *

router = APIRouter(prefix="/properties", tags=["properties"])
rentals_united_service = RentalsUnitedService()

@router.post("/blocked-apartments")
async def get_blocked_apartments(request: BlockedApartmentsRequest):
    """Returns apartments that are either available or blocked for users dates"""
    date_from_obj = datetime(**request.date_from.dict())
    date_to_obj = datetime(**request.date_to.dict())
    
    result = await rentals_united_service.get_blocked_apartments(date_from_obj, date_to_obj)
    return result
        
    
@router.post("/check-calendar")
async def check_calendar(request: CheckCalendarRequest):
    """Returns the availability calendar for specific apartment"""
    date_from = datetime.today()
    date_to = date_from + relativedelta(years=5)
    
    result = await rentals_united_service.check_availability(request.apartment_id, date_from, date_to)
    return result
    
@router.post("/check-price")
async def check_price(request: CheckPriceRequest):
    """Returns the price for specific apartment"""

    return await rentals_united_service.check_price(request.apartment_id)