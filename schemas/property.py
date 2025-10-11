from pydantic import BaseModel
from datetime import datetime

class DateModel(BaseModel):
    day: int
    month: int 
    year: int

    def to_datetime(self) -> datetime:
        return datetime(year=self.year, month=self.month, day=self.day)

class BlockedApartmentsRequest(BaseModel):
    date_from: DateModel
    date_to: DateModel

class CheckCalendarRequest(BaseModel):
    apartment_id: int

class CheckPriceRequest(BaseModel):
    apartment_id: int