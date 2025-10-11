import logging
from typing import Dict, Any
import stripe
import secrets
import hashlib
from schemas.payments import CreateCheckoutRequest, DateModel
from services.integrations.rentals_united_service import RentalsUnitedService
from services.integrations.supabase_service import SupabaseService
from config import settings
from datetime import datetime
from services.integrations.rentals_united.property_price import Pull_ListPropertyPrices_RQ


logger = logging.getLogger(__name__)

class BookingService:
    def __init__(self):
        self.rentals_united_service = RentalsUnitedService()
        self.supabase_service = SupabaseService()
        stripe.api_key = settings.sk
    

    

    