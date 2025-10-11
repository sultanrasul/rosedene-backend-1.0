import logging
from datetime import datetime
import hashlib
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
import requests
from datetime import datetime
from schemas.reviews import *
from utils.exceptions import *
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)

class ReviewsService:

    async def _get_reviews(
        self,
        request: GetReviewsRequest,
    ) -> Dict[str, Any]:
        """Create booking record in supabase before confirming in rentals united"""

        topics = request.topics
        search_term = request.search_term
        sort_by = request.sort_by
        sort_order = request.sort_order
        page = request.page
        limit = request.limit


        # Read and clean data
        df = pd.read_csv("data/reviews.csv", keep_default_na=False)
        
        # Convert columns
        numeric_cols = ["Review score", "Staff", "Cleanliness", "Location", 
                       "Facilities", "Comfort", "Value for money"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Handle dates
        df['Review date'] = pd.to_datetime(df['Review date'], errors='coerce')
        df = df.dropna(subset=['Review date'])


        # Initialize masks
        topics_mask = pd.Series(False, index=df.index)
        search_mask = pd.Series(False, index=df.index)

        # Build topics mask (OR between topics)
        if request.topics:
            for topic in topics:
                topic_lower = topic.lower()
                topic_mask = (
                    df['Review title'].str.lower().str.contains(topic_lower, na=False) |
                    df['Positive review'].str.lower().str.contains(topic_lower, na=False)
                )
                topics_mask |= topic_mask

        # Build search mask
        if search_term:
            search_mask = (
                df['Review title'].str.lower().str.contains(search_term, na=False) |
                df['Positive review'].str.lower().str.contains(search_term, na=False)
            )

        # Combine masks with OR logic
        if topics and search_term:
            combined_mask = topics_mask | search_mask
        elif topics:
            combined_mask = topics_mask
        elif search_term:
            combined_mask = search_mask
        else:
            combined_mask = pd.Series(True, index=df.index)  # Show all if no filters

        # Apply the combined filter
        df = df[combined_mask]
        
        sort_columns = {
            "date": "Review date",
            "rating": "Review score"
        }
        
        if sort_by in sort_columns:
            sort_column = sort_columns[sort_by]
            df = df.sort_values(
                sort_column, 
                ascending=(sort_order == "asc")
            )

        # Pagination
        start = (page - 1) * limit
        end = start + limit

        # Convert to records
        reviews = df.iloc[start:end].to_dict(orient="records")

        response = {
            "reviews": reviews,
            "page": page,
            "limit": limit,
            "total": len(df),
            "sort_by": sort_by,
            "sort_order": sort_order,
            "search_term": search_term,
            "topics": topics
        }

        return response
