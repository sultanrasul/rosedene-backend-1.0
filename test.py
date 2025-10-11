from schemas.booking import Booking
from services.integrations.brevo_service import BrevoService

from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

booking = Booking(
    id=uuid4(),
    user_id=None,
    name="John Doe",
    email="sultanrasul5@gmail.com",
    phone="+441234567890",
    zip_code="W1A 1AA",
    country="UK",
    apartment_id=101,
    date_from=datetime.now(),
    date_to=datetime.now() + timedelta(days=3),
    nights=3,
    adults=2,
    children=1,
    children_ages=[5],
    special_requests="Late check-in",
    refundable=True,
    client_price=Decimal("299.99"),
    ru_price=Decimal("250.00"),
    ru_booking_reference="RU12345612",
    ru_status="confirmed",
    payment_intent_id="pi_3NkD1m2eZvKYlo2C1example",
    payment_status="captured",
    client_secret="test_secret_123",
)


cancel = False

brevo_service = BrevoService(booking, cancel).send_email()