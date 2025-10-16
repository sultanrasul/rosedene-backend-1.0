from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import properties, bookings, payments, reviews
from config import settings
from utils.exceptions import http_exception_handler
import uvicorn

app = FastAPI(title="Direct Booking API")



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(properties.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "healthy"}