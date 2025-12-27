from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.post import PostStatus, PostType


class CreatePostAnalysisRequest(BaseModel):
    postUrl: str
    externalRefId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class CommentAnalysisResponse(BaseModel):
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


class PostAnalysisResultResponse(BaseModel):
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
    comments: List[CommentAnalysisResponse] = Field(default_factory=list)


class PostStatusResponse(BaseModel):
    id: str
    postUrl: str
    postType: PostType
    platform: str
    status: PostStatus
    analysis: Optional[PostAnalysisResultResponse] = None
    errorMessage: Optional[str] = None
    externalRefId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class PostListItem(BaseModel):
    id: str
    postUrl: str
    postType: PostType
    platform: str
    status: PostStatus
    errorMessage: Optional[str] = None
    externalRefId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    # Summary stats
    comments_count: int = 0
    flagged_commenters_count: int = 0
