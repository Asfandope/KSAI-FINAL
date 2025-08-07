from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.content import Content

router = APIRouter()


@router.get("/", response_model=List[str])
async def get_topics(db: Session = Depends(get_db)):
    """Get list of available content topics"""
    # For now, return hardcoded topics
    # Later, this will fetch from the database
    topics = ["Politics", "Environmentalism", "SKCRF", "Educational Trust"]
    return topics


@router.get("/categories", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    """Get list of content categories from database"""
    try:
        categories = db.query(Content.category).distinct().all()
        return (
            [category[0] for category in categories]
            if categories
            else ["Politics", "Environmentalism", "SKCRF", "Educational Trust"]
        )
    except Exception:
        # Fallback to hardcoded categories if database connection fails
        return ["Politics", "Environmentalism", "SKCRF", "Educational Trust"]
