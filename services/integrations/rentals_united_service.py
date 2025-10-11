import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException, status
import requests
from schemas.booking import Booking, RentalsUnitedBooking
from utils.exceptions import *

# Import your existing classes
from services.integrations.rentals_united.location_check import Pull_ListPropertiesBlocks_RQ
from services.integrations.rentals_united.property_check import Pull_ListPropertyAvailabilityCalendar_RQ
from services.integrations.rentals_united.property_price import Pull_ListPropertyPrices_RQ
from services.integrations.rentals_united.add_booking import Push_PutConfirmedReservationMulti_RQ
from services.integrations.rentals_united.cancel_booking import Push_CancelReservation_RQ
from services.integrations.rentals_united.get_booking import Pull_GetReservationByID_RQ

from config import settings

logger = logging.getLogger(__name__)

class RentalsUnitedService:
    def __init__(self):
        self.username = settings.username
        self.password = settings.password
        self.endpoint = settings.ru_endpoint
        
        # Apartment IDs dictionary
        self.apartment_ids = {
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

    async def check_price(self, apartment_id: int):
        all_prices = Pull_ListPropertyPrices_RQ.get_all_prices()
        if not all_prices or str(apartment_id) not in all_prices:
            logging.error(f"❌ No price data found for this property")
            raise NoPriceDataFound

        prices = all_prices[str(apartment_id)]

        # Safely extract Seasons
        property_prices = prices.get("Prices", {})
        seasons = property_prices.get("Season")

        if not seasons:
            raise NoPriceDataFound
        
        return prices

    async def get_blocked_apartments(self, date_from: datetime, date_to: datetime) -> Dict[str, Any]:
        """Get available/blocked apartments - replaces /blocked_apartments endpoint logic"""
        try:
            props_request = Pull_ListPropertiesBlocks_RQ(
                self.username, self.password, 
                location_id=7912,
                date_from=date_from,
                date_to=date_to
            )
            
            response = await self._make_ru_request(props_request)
            properties = props_request.check_blocked_properties(response.text, self.apartment_ids)
            
            # Add prices
            prices = await self.get_property_prices()

            properties['available'] = self._enhance_with_prices(properties['available'], prices)
            properties['blocked'] = self._enhance_with_prices(properties['blocked'], prices)

            print(f"check_blocked_properties returned: {properties!r}")

            return properties
            
        except Exception as e:
            logger.error(f"Error getting blocked apartments: {e}")
            raise

    def _enhance_with_prices(self, apartments: list, prices: dict) -> list:
        """Add price information to apartments list"""
        enhanced_apartments = []

        for apartment in apartments:
            apartment_id = str(apartment['id'])
            
            # Safe price lookup with default
            apartment_prices = prices.get(apartment_id, {})
            price_list = apartment_prices.get('Prices', [])
            
            # Create a copy to avoid mutating original
            enhanced_apartment = apartment.copy()
            enhanced_apartment['Prices'] = price_list  # Always list, never string
            
            enhanced_apartments.append(enhanced_apartment)
        
        return enhanced_apartments
    
    async def check_availability(self, property_id: int, date_from: datetime, date_to: datetime) -> list:
        """Check if a property is available for dates"""
        if property_id not in self.apartment_ids:
            raise ApartmentNotFound()

        avail_request = Pull_ListPropertyAvailabilityCalendar_RQ(
            self.username, self.password,
            property_id=property_id,
            date_from=date_from,
            date_to=date_to
        )
        
        response = await self._make_ru_request(avail_request)
        calendar = avail_request.check_availability_calendar(response.text)
        
        return calendar
    
    async def get_property_prices(self) -> Dict:
        """Get all property prices"""
        return Pull_ListPropertyPrices_RQ.get_all_prices()
    
    async def create_booking(self, booking: Booking) -> str:
        """Create a new booking in Rentals United"""

        # Validate and convert booking data to a dict
        reservation = Push_PutConfirmedReservationMulti_RQ(
            self.username,
            self.password,
            property_id=booking.apartment_id,
            date_from=booking.date_from,
            date_to=booking.date_to,
            number_of_guests=(booking.adults + booking.children),
            client_price=booking.client_price,
            ru_price=booking.ru_price,
            already_paid=booking.client_price,
            customer_name=booking.name,
            customer_surname=" ",  # RU requires surname
            customer_email=booking.email,
            customer_phone=booking.phone,
            customer_zip_code=booking.zip_code,
            number_of_adults=booking.adults,
            number_of_children=booking.children,
            children_ages=booking.children_ages if booking.children_ages else [],
            comments=booking.special_requests,
            commission=0
        )

        response = await self._make_ru_request(reservation)
        json_response = reservation.booking_reference(response.text)

        # Validate the RU response
        status_info = json_response["Push_PutConfirmedReservationMulti_RS"]["Status"]
        status_code = int(status_info["@ID"])
        status_text = status_info["#text"]

        if status_code != 0:
            # Booking failed: raise a custom exception
            raise RentalsUnitedError(status_code, status_text)

        return json_response["Push_PutConfirmedReservationMulti_RS"]["ReservationID"]
    
    async def cancel_booking(self, booking_ref: str) -> bool:
        """Cancel a booking in Rentals United"""
        cancel_request = Push_CancelReservation_RQ(
            self.username, self.password, 
            booking_ref, 
            cancel_type_id=2
        )
        
        response = await self._make_ru_request(cancel_request)
        cancel_data = cancel_request.get_details(response.text)
        
        status_code = int(cancel_data["Push_CancelReservation_RS"]["Status"]["@ID"])
        return status_code == 0
    
    async def _make_ru_request(self, request_object) -> requests.Response:
        """Helper method to make RU API requests"""
        return requests.post(
            self.endpoint,
            data=request_object.serialize_request(),
            headers={"Content-Type": "application/xml"},
            timeout=30
        )

# Define a custom exception for RU errors
class RentalsUnitedError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"RU Booking failed ({code}): {message}")