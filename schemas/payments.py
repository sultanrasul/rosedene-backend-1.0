from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class DateModel(BaseModel):
    day: int = Field(example=1)
    month: int = Field(example=9)
    year: int = Field(example=2027)

    def to_datetime(self) -> datetime:
        return datetime(year=self.year, month=self.month, day=self.day)


class CreateCheckoutRequest(BaseModel):
    apartment_id: int = Field(example=3070531)
    date_from: DateModel
    date_to: DateModel
    adults: int = Field(ge=1, le=6, example=2)  # at least 1 adult, max 6
    children: int = Field(ge=0, le=6, example=1)
    children_ages: Optional[List[int]] = Field(default=[], example=[6])
    user_id: Optional[str] = Field(default=None, example="user_12345")
    name: str = Field(example="John Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    phone: str = Field(example="+1234567890")
    special_requests: Optional[str] = Field(default=None, example="Late check-in if possible")
    refundable: bool = Field(example=True)

    model_config = ConfigDict(extra="forbid")

class BlockedApartmentsRequest(BaseModel):
    date_from: DateModel
    date_to: DateModel

class CheckCalendarRequest(BaseModel):
    apartment_id: int

class CheckPriceRequest(BaseModel):
    apartment_id: int
