from schemas.booking import Booking
from services.integrations.brevo_service import BrevoService
from services.integrations.supabase_service import SupabaseService

from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

supabase_service = SupabaseService()

import asyncio

async def main():
	output = await supabase_service._validate_user("eyJhbGciOiJIUzI1NiIsImtpZCI6ImpsYmFHMitCY2xsSkJrSW0iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL29vdnRvaGZzbmRncWl6bGdtaW93LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI1YjYxNmIwZi05MzA2LTRkYTEtYWNhNi04MjE2N2VjYjYzZjMiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzYwMzE3NDEzLCJpYXQiOjE3NjAzMTM4MTMsImVtYWlsIjoic3BvdGlmeWlzZ29vZDIxNTcyNUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6Imdvb2dsZSIsInByb3ZpZGVycyI6WyJnb29nbGUiXX0sInVzZXJfbWV0YWRhdGEiOnsiYXZhdGFyX3VybCI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0s5dmJSTzNYbF8zRHE1SnJFNFNiVlU2MHBlQTUyelZpNFFMSW0wQ1RpNnBEMXAzZz1zOTYtYyIsImVtYWlsIjoic3BvdGlmeWlzZ29vZDIxNTcyNUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiQm9iIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6IkJvYiIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0s5dmJSTzNYbF8zRHE1SnJFNFNiVlU2MHBlQTUyelZpNFFMSW0wQ1RpNnBEMXAzZz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTAwNDU0MDEzNTU2MzUyMzI1NzM5Iiwic3ViIjoiMTAwNDU0MDEzNTU2MzUyMzI1NzM5In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NjAzMDUwNzZ9XSwic2Vzc2lvbl9pZCI6ImJhOTIzNzRlLTYyOTMtNGU2ZS1hY2VkLTQ3MjBmM2U1YmIzYyIsImlzX2Fub255bW91cyI6ZmFsc2V9.iGeGF97qLMQreFlE0CvZvKzyE7u_jBSBIhQogoWE4T0")
	print(output)

asyncio.run(main())

# booking = Booking(
#     id=uuid4(),
#     user_id=None,
#     name="John Doe",
#     email="sultanrasul5@gmail.com",
#     phone="+441234567890",
#     zip_code="W1A 1AA",
#     country="UK",
#     apartment_id=101,
#     date_from=datetime.now(),
#     date_to=datetime.now() + timedelta(days=3),
#     nights=3,
#     adults=2,
#     children=1,
#     children_ages=[5],
#     special_requests="Late check-in",
#     refundable=True,
#     client_price=Decimal("299.99"),
#     ru_price=Decimal("250.00"),
#     ru_booking_reference="RU12345612",
#     ru_status="confirmed",
#     payment_intent_id="pi_3NkD1m2eZvKYlo2C1example",
#     payment_status="captured",
#     client_secret="test_secret_123",
# )


# cancel = False

# brevo_service = BrevoService(booking, cancel).send_email()

