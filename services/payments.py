import logging
from typing import Dict, Any
from fastapi import HTTPException
import stripe
import secrets
import hashlib
from schemas.payments import CreateCheckoutRequest, DateModel
from config import settings
from datetime import datetime, date
from services.integrations.rentals_united.property_price import Pull_ListPropertyPrices_RQ
from services.integrations.brevo_service import BrevoService
from services.integrations.rentals_united_service import RentalsUnitedError, RentalsUnitedService
from services.integrations.supabase_service import SupabaseService


logger = logging.getLogger(__name__)

rentals_united_service = RentalsUnitedService()
supabase_service = SupabaseService()

class PaymentService:
    def __init__(self):
        stripe.api_key = settings.sk
        self.sk = settings.sk
        self.pk = settings.pk
        self.whsec = settings.whsec
    
    async def create_checkout_session(self, booking_data: CreateCheckoutRequest) -> Dict[str, Any]:
        """
        Create Stripe checkout session and provisional booking
        """
        apartment_id = booking_data.apartment_id
        date_to = booking_data.date_to
        date_from = booking_data.date_from
        adults = booking_data.adults
        children = booking_data.children
        childrenAges = booking_data.children_ages

        user_id = booking_data.user_id
        name = booking_data.name
        email = booking_data.email
        phone = booking_data.phone
        special_requests = booking_data.special_requests
        refundable = booking_data.refundable
        date_from_obj = booking_data.date_from.to_datetime()
        date_to_obj = booking_data.date_to.to_datetime()

            

        # 2. Check availability
        await self._check_availability(apartment_id, date_from_obj, date_to_obj)
        
        # 3. Calculate price
        basePrice, customerPrice = await self._calculate_price(apartment_id, adults, children, date_from_obj, date_to_obj, refundable)
        
        # 4. Create provisional booking in database
        booking_uuid = await supabase_service.create_provisional_booking(booking_data, basePrice, customerPrice)
        
        # 5. Create Stripe PaymentIntent
        payment_intent = self._create_stripe_payment_intent(
            customerPrice, 
            booking_data,
            booking_uuid
        )
        
        # 6. Update booking with payment intent info
        await supabase_service.update_booking(booking_uuid, payment_intent_id=payment_intent.id, client_secret=payment_intent.client_secret)

        # 7. If this is a guest booking (no user_id), generate a secure token
        token = None
        if not user_id:
            token = secrets.token_hex(16)  # 32-char random hex string
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Store only the hash in Supabase
            await supabase_service.update_booking(
                booking_uuid,
                secret_token_hash=token_hash
            )

        response = {
            "clientSecret": payment_intent.client_secret,
            "booking_uuid": booking_uuid,
            "amount": f"{customerPrice:.2f}"
        }

        if token:
            response["token"] = token  # send only for guests

        return response
    
    async def complete_checkout_session(self, event: dict):

        # 1. Retrieve payment intent
        payment_intent_id = event["data"]["object"].get("payment_intent")
        meta = event["data"]["object"].get("metadata")

        booking_uuid = meta["booking_uuid"]
        booking = await supabase_service.get_booking_uuid_data(booking_id=booking_uuid) # Returns Booking Data Schema

        # Get Billing Details from Stripe (e.g. Country Postal Code) -> Update Data on Supabase
        billing_details = event["data"]["object"].get("billing_details")
        country = billing_details["address"]["country"]
        postal_code = billing_details["address"]["postal_code"]
        await supabase_service.update_booking(booking_id=booking_uuid, zip_code=postal_code, country=country)


        # Add Booking To Rentals United through the Rentals United service
        try:
            booking_reference = await rentals_united_service.create_booking(booking)
        except RentalsUnitedError as e:
            # Cancel the Stripe payment and provide feedback
            print(f"🚨 Rentals United Error: #{e.code} - {e.message}")
            await self._cancel_payment_intent(payment_intent_id, reason=e.message)

            raise HTTPException(status_code=409, detail=e.message)

        # Update Supabase Booking Record
        await supabase_service.update_booking(booking_id=booking_uuid, ru_booking_reference=booking_reference, ru_status="confirmed")

        # Capture payment, Update Supabase and Stripe metadata
        await self._capture_payment_intent(payment_intent_id, booking_reference, booking_uuid)

        # Send Email Using Brevos Service also fetch again after updating the booking record
        booking = await supabase_service.get_booking_uuid_data(booking_id=booking_uuid)
        brevo_service = BrevoService(booking, cancel=False)
        brevo_service.send_email()

        return {
                "message": "Booking completed", 
                "reference": booking_reference
            }

    def _validate_booking_data(self, data: Dict):
        """Validate booking request data"""
        # Your existing validation logic here
        pass
    
    async def _check_availability(self, apartment_id: int, date_from: datetime, date_to: datetime):
        """Check property availability for specific days"""

        calendar = await rentals_united_service.check_availability(apartment_id, date_from, date_to)

        if not calendar:
            raise ValueError("No availability calendar returned — apartment not bookable")
        print("CALENDAR: ", calendar)


        if any(day.get("IsBlocked") == "true" for day in calendar):
            raise ValueError("Apartment not available for selected dates")
    
    async def _calculate_price(self, apartment_id: int, adults: int, children: int, date_from: datetime, date_to: datetime, refundable: bool) -> Dict:
        """Calculate booking price"""
        basePrice = Pull_ListPropertyPrices_RQ.calculate_ru_price(
            property_id=apartment_id, 
            guests=adults+children,
            date_from=date_from, 
            date_to=date_to
        )
            
        customerPrice = Pull_ListPropertyPrices_RQ.calculate_client_price(
            basePrice=basePrice, 
            refundable=refundable
        )
        return basePrice, customerPrice
    
    def _create_stripe_payment_intent(self, amount: float, booking_data: CreateCheckoutRequest, booking_uuid: str):
        """Create Stripe PaymentIntent"""
        return stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency='gbp',
            payment_method_types=['card'],
            metadata={
                "booking_uuid": booking_uuid,
                "user_id": booking_data.user_id,
                "property_id": booking_data.apartment_id
            },
            description=f"Booking for {rentals_united_service.apartment_ids[booking_data.apartment_id]}",
            capture_method='manual'
        )
    
    async def _capture_payment_intent(self, payment_intent_id: str, booking_reference: str, booking_uuid: str):
        """Helper to capture Stripe payment, update booking status and metadata"""
        try:
            # Update metadata with booking reference
            stripe.PaymentIntent.modify(
                payment_intent_id,
                metadata={"booking_reference": booking_reference}
            )

            # Capture the payment
            captured_intent = stripe.PaymentIntent.capture(payment_intent_id)

            # Check status
            if captured_intent.status != 'succeeded':
                raise Exception(f"Capture failed with status: {captured_intent.status}")

            logger.info({
                "message": "✅ Booking confirmed",
                "booking_reference": booking_reference,
                "payment_intent_id": payment_intent_id
            })

            # Update booking in Supabase
            await supabase_service.update_booking(booking_uuid, payment_status="captured")

        except stripe.error.StripeError as e:
            logger.exception(f"⚠️ Payment capture failed for {payment_intent_id}")
            await supabase_service.update_booking(booking_uuid, payment_status="failed")

            # Here you could also alert admin (email/SMS)
            raise HTTPException(status_code=500, detail="Payment capture failed")

    async def _cancel_payment_intent(self, payment_intent_id: str, reason: str):
        """Helper to cancel a Stripe payment intent and log reason"""
        try:
            stripe.PaymentIntent.cancel(payment_intent_id)
            logger.warning(f"PaymentIntent {payment_intent_id} cancelled due to: {reason}")
            # Update booking status
            await supabase_service.update_booking(booking_id=payment_intent_id, payment_status="cancelled")
        except stripe.error.StripeError as e:
            logger.exception(f"Failed to cancel PaymentIntent {payment_intent_id}: {str(e)}")
