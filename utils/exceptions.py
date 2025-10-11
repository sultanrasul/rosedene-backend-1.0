from fastapi import HTTPException

class BookingNotFound(Exception): pass
class PaymentFailed(Exception): pass
class ApartmentNotFound(Exception): pass
class NoPriceDataFound(Exception): pass

def http_exception_handler(exc: Exception):
    if isinstance(exc, BookingNotFound):
        return HTTPException(status_code=404, detail="Booking not found")
    if isinstance(exc, PaymentFailed):
        return HTTPException(status_code=400, detail="Payment failed")
    if isinstance(exc, ApartmentNotFound):
        return HTTPException(status_code=400, detail="Apartment Not Found")
    if isinstance(exc, NoPriceDataFound):
        return HTTPException(status_code=400, detail="No price data found for this apartment")

    return HTTPException(status_code=500, detail="Internal server error")