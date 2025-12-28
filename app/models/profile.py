from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import BaseModel, Field


class ProfileStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProfileUrls(BaseModel):
    instagramUrl: Optional[str] = None
    facebookUrl: Optional[str] = None
    twitterUrl: Optional[str] = None
    linkedinUrl: Optional[str] = None
    redditUrl: Optional[str] = None
    blogUrls: Optional[List[str]] = None


class Profile(Document):
    externalRefId: Optional[str] = Field(default=None)
    subjectName: Optional[str] = Field(default=None)
    userId: Optional[str] = Field(default=None)
    urls: ProfileUrls
    status: ProfileStatus = Field(default=ProfileStatus.PENDING)
    errorMessage: Optional[str] = Field(default=None)
    summary: Optional[Dict[str, Any]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profiles"

    async def mark_status(self, status: ProfileStatus, error_message: Optional[str] = None) -> None:
        self.status = status
        self.updatedAt = datetime.utcnow()
        if error_message:
            self.errorMessage = error_message
        await self.save()
