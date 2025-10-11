from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal, Optional, List
from datetime import datetime

class GetReviewsRequest(BaseModel):
    """
    Request model for filtering, searching, sorting, and paginating reviews.
    """

    # Filtering
    search_term: Optional[str] = Field(default="", example="clean room")
    topics: Optional[List[str]] = Field(default=[], example=["location", "breakfast"])

    # Sorting (validated using Literal)
    sort_by: Literal["date", "rating"] = Field(default="date", example="date")
    sort_order: Literal["asc", "desc"] = Field(default="desc", example="desc")

    # Pagination
    page: int = Field(default=1, ge=1, example=1)
    limit: int = Field(default=10, ge=1, le=100, example=10)

    model_config = ConfigDict(extra="forbid")

class CreateCheckoutRequest(BaseModel):
    apartment_id: int = Field(example=3070531)
    adults: int = Field(ge=1, le=6, example=2)  # at least 1 adult, max 6
    children: int = Field(ge=0, le=6, example=1)
    children_ages: Optional[List[int]] = Field(default=[], example=[6])
    user_id: Optional[str] = Field(default=None, example="user_12345")
    name: str = Field(example="John Doe")
    phone: str = Field(example="+1234567890")
    special_requests: Optional[str] = Field(default=None, example="Late check-in if possible")
    refundable: bool = Field(example=True)