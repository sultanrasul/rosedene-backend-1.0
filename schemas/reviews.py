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
