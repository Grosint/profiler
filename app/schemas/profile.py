from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.profile import ProfileStatus
from app.models.profile_trait import TraitType


class ProfileUrlsIn(BaseModel):
    instagramUrl: Optional[str] = None
    facebookUrl: Optional[str] = None
    twitterUrl: Optional[str] = None
    linkedinUrl: Optional[str] = None
    redditUrl: Optional[str] = None
    blogUrls: Optional[List[str]] = None


class CreateProfileRequest(BaseModel):
    subjectName: Optional[str] = None
    externalRefId: Optional[str] = None
    urls: ProfileUrlsIn
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class ProfileSummary(BaseModel):
    status: ProfileStatus
    summary: Optional[Dict[str, Any]] = None
    createdAt: datetime
    updatedAt: datetime


class TraitOverviewItem(BaseModel):
    traitType: TraitType
    averageScore: float


class ProfileStatusResponse(BaseModel):
    id: str
    status: ProfileStatus
    summary: Optional[Dict[str, Any]] = None
    traitsOverview: List[TraitOverviewItem] = Field(default_factory=list)
    errorMessage: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class TraitDetail(BaseModel):
    traitType: TraitType
    traitName: str
    score: float
    confidence: float
    evidenceSnippets: List[str]
    extra: Dict[str, Any]


class ProfileDetailsResponse(BaseModel):
    id: str
    subjectName: Optional[str]
    externalRefId: Optional[str]
    userId: Optional[str]
    status: ProfileStatus
    summary: Optional[Dict[str, Any]]
    traits: List[TraitDetail]
    narratives: Dict[str, str] = Field(
        default_factory=dict,
        description="High-level textual explanation fields like personalityNarrative, riskNarrative, etc.",
    )
    createdAt: datetime
    updatedAt: datetime


class ProfileListItem(BaseModel):
    id: str
    subjectName: Optional[str]
    externalRefId: Optional[str]
    status: ProfileStatus
    traitsOverview: List[TraitOverviewItem] = Field(default_factory=list)
    errorMessage: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
