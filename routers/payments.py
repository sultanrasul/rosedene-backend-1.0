from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from dateutil.relativedelta import relativedelta
from services.payments import PaymentService
from services.integrations.rentals_united_service import RentalsUnitedService
from schemas.payments import *
import stripe
import logging
import os

router = APIRouter(prefix="/payments", tags=["payments"])
rentals_united_service = RentalsUnitedService()
payments = PaymentService()

@router.post("/create-checkout-session")
async def create_checkout_session(request: CreateCheckoutRequest):
    """
    Create a Stripe checkout session
    """
    # try:
        # Pass the Pydantic model directly
    result = await payments.create_checkout_session(request)
        
    return result
    # except ValueError as e:
    #     raise HTTPException(status_code=400, detail=str(e))
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail="Internal server error")

# Complete checkout session
@router.post("/complete-checkout-session")
async def complete_checkout_session(request: Request):
    payload = await request.body()  # 🔹 raw bytes
    sig_header = request.headers.get("Stripe-Signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, payments.whsec
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Only handle charge.succeeded
    if event["type"] != "charge.succeeded":
        return {"message": f"Ignored event {event['type']}"}

    result = await payments.complete_checkout_session(event)

    return result
