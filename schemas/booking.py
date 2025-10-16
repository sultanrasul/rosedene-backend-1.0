from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

class Booking(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    apartment_id: int
    date_from: datetime
    date_to: datetime
    nights: int
    adults: int
    children: int = 0
    children_ages: Optional[List[int]] = None  # JSONB stored as list of ints
    special_requests: Optional[str] = None
    refundable: bool = False
    client_price: Decimal
    ru_price: Optional[Decimal] = None
    ru_booking_reference: Optional[str] = None
    ru_status: str = "pending"
    payment_intent_id: Optional[str] = None
    payment_status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client_secret: Optional[str] = None
    secret_token_hash: Optional[str] = None


class RentalsUnitedBooking(BaseModel):
    property_id: int = Field(..., description="Rentals United property ID")
    date_from: date = Field(..., description="Start date of the stay (YYYY-MM-DD)")
    date_to: date = Field(..., description="End date of the stay (YYYY-MM-DD)")
    number_of_guests: int = Field(..., description="Total number of guests")
    
    ru_price: float = Field(..., description="Base (Rentals United) price")
    client_price: float = Field(..., description="Final price charged to client")
    already_paid: bool = Field(False, description="Whether the booking is already paid")
    commission: float = Field(..., description="Commission charged by the channel")

    customer_name: str = Field(..., description="Guest first name")
    customer_surname: str = Field(..., description="Guest last name")
    customer_email: EmailStr
    customer_phone: str
    customer_zip_code: Optional[str] = None

    number_of_adults: int
    number_of_children: int = 0
    children_ages: Optional[List[int]] = []
    comments: Optional[str] = None

    def to_dict(self):
        """Convert to plain dict ready for RU XML serialization"""
        data = self.dict()
        # Ensure datetime objects are converted to date strings
        if isinstance(data["date_from"], (datetime, date)):
            data["date_from"] = data["date_from"].strftime("%Y-%m-%d")
        if isinstance(data["date_to"], (datetime, date)):
            data["date_to"] = data["date_to"].strftime("%Y-%m-%d")
        return data