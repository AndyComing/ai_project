from typing import List, Optional
from pydantic import BaseModel


class TrendItem(BaseModel):
    topic: str
    description: str
    data_support: Optional[str] = None


class ResearchResponse(BaseModel):
    title: str
    query: str
    trends: List[TrendItem]
    conclusion: str
    sources: List[str] = []