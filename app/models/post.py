from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import BaseModel, Field


class PostStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class PostType(str, Enum):
    PROFILE = "profile"
    POST = "post"


class CommentAnalysis(BaseModel):
    """Analysis result for a single comment."""
    comment_id: str
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    text: str
    timestamp: Optional[datetime] = None
    toxicity_score: float = 0.0
    is_toxic: bool = False
    is_anti_national: bool = False
    toxicity_labels: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment: str = "neutral"
    sentiment_score: float = 0.0


class PostAnalysisResult(BaseModel):
    """Analysis result for a post."""
    post_id: str
    post_url: str
    post_text: str
    author_username: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    comments_count: int = 0
    comments_analyzed: int = 0
    toxic_comments_count: int = 0
    anti_national_comments_count: int = 0
    flagged_commenters: List[Dict[str, Any]] = Field(default_factory=list)
    comments: List[CommentAnalysis] = Field(default_factory=list)


class Post(Document):
    """Post analysis document."""
    postUrl: str
    postType: PostType = Field(default=PostType.POST)
    platform: str  # twitter, facebook, instagram, etc.
    status: PostStatus = Field(default=PostStatus.PENDING)
    errorMessage: Optional[str] = Field(default=None)

    # Analysis results
    analysis: Optional[PostAnalysisResult] = Field(default=None)

    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    externalRefId: Optional[str] = Field(default=None)

    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "posts"

    async def mark_status(self, status: PostStatus, error_message: Optional[str] = None) -> None:
        self.status = status
        self.updatedAt = datetime.utcnow()
        if error_message:
            self.errorMessage = error_message
        await self.save()
