from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from beanie import Document, Link
from pydantic import Field

from .profile import Profile


class TraitType(str, Enum):
    PERSONALITY = "personality"
    WORK_STYLE = "work_style"
    COMMUNICATION = "communication"
    RISK = "risk"
    CULTURAL_FIT = "cultural_fit"
    LEADERSHIP = "leadership"


class ProfileTrait(Document):
    profile: Link[Profile]
    traitType: TraitType
    traitName: str
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidenceSnippets: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "profile_traits"
