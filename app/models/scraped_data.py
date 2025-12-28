from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from beanie import Document, Link
from pydantic import Field

from .profile import Profile


class ScrapePlatform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    BLOG = "blog"
    LINKEDIN = "linkedin"
    REDDIT = "reddit"
    UNKNOWN = "unknown"


class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ScrapedData(Document):
    profile: Link[Profile]
    platform: ScrapePlatform = Field(default=ScrapePlatform.UNKNOWN)
    url: str
    rawContent: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    scrapedAt: datetime = Field(default_factory=datetime.utcnow)
    scrapeStatus: ScrapeStatus = Field(default=ScrapeStatus.SUCCESS)
    errorMessage: Optional[str] = Field(default=None)

    class Settings:
        name = "scraped_data"
