import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # Rentals United API
    username: str
    password: str
    ru_endpoint: str = "https://new.rentalsunited.com/api/handler.ashx"
    
    # Stripe
    pk: str
    sk: str
    whsec: str
    
    # Supa Base
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT: str
    
    # Brevo Email Service 
    email: str
    
    # Frontend
    frontend_url: str = "https://www.rosedenedirect.com"
    
    # Environment
    ENV: str = "testing"
    
    class Config:
        env_file = ".env"

settings = Settings()