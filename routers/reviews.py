from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from dateutil.relativedelta import relativedelta
from services.reviews import ReviewsService
from schemas.reviews import *

router = APIRouter(prefix="/reviews", tags=["reviews"])
reviews_service = ReviewsService()

@router.post("/get-reviews")
async def get_reviews(request: GetReviewsRequest):
    """Returns Reviews"""
    
    result = await reviews_service._get_reviews(request)

    return result