from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel

from app.models.scraped_data import ScrapePlatform, ScrapeStatus


class ScrapedDataItem(BaseModel):
    id: str
    platform: ScrapePlatform
    url: str
    rawContent: str
    metadata: Dict[str, Any]
    scrapedAt: datetime
    scrapeStatus: ScrapeStatus
    errorMessage: str | None = None
