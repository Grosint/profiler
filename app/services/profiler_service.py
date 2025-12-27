from typing import List, Optional

from beanie import PydanticObjectId

from app.models.profile import Profile, ProfileStatus, ProfileUrls
from app.models.profile_trait import ProfileTrait
from app.models.scraped_data import ScrapedData
from app.schemas.profile import (
    CreateProfileRequest,
    ProfileDetailsResponse,
    ProfileStatusResponse,
    ProfileListItem,
    TraitDetail,
    TraitOverviewItem,
)
from app.schemas.scraped_data import ScrapedDataItem


async def create_profile_job(payload: CreateProfileRequest) -> Profile:
    # Convert ProfileUrlsIn to ProfileUrls
    profile_urls = ProfileUrls(
        instagramUrl=payload.urls.instagramUrl,
        facebookUrl=payload.urls.facebookUrl,
        twitterUrl=payload.urls.twitterUrl,
        blogUrls=payload.urls.blogUrls,
    )
    profile = Profile(
        externalRefId=payload.externalRefId,
        subjectName=payload.subjectName,
        urls=profile_urls,
        metadata=payload.metadata,
    )
    await profile.insert()
    return profile


async def get_profile_status(profile_id: str) -> ProfileStatusResponse:
    profile = await Profile.get(PydanticObjectId(profile_id))
    if not profile:
        raise ValueError("Profile not found")

    traits = await ProfileTrait.find(ProfileTrait.profile.id == profile.id).to_list()
    overview: List[TraitOverviewItem] = []
    if traits:
        by_type = {}
        for t in traits:
            by_type.setdefault(t.traitType, []).append(t.score)
        for trait_type, scores in by_type.items():
            avg = sum(scores) / len(scores)
            overview.append(TraitOverviewItem(traitType=trait_type, averageScore=avg))

    return ProfileStatusResponse(
        id=str(profile.id),
        status=profile.status,
        summary=profile.summary,
        traitsOverview=overview,
        errorMessage=profile.errorMessage,
        createdAt=profile.createdAt,
        updatedAt=profile.updatedAt,
    )


async def get_profile_details(profile_id: str) -> ProfileDetailsResponse:
    profile = await Profile.get(PydanticObjectId(profile_id))
    if not profile:
        raise ValueError("Profile not found")

    traits = await ProfileTrait.find(ProfileTrait.profile.id == profile.id).to_list()
    trait_items: List[TraitDetail] = [
        TraitDetail(
            traitType=t.traitType,
            traitName=t.traitName,
            score=t.score,
            confidence=t.confidence,
            evidenceSnippets=t.evidenceSnippets,
            extra=t.extra,
        )
        for t in traits
    ]

    narratives = profile.summary.get("narratives", {}) if profile.summary else {}

    return ProfileDetailsResponse(
        id=str(profile.id),
        subjectName=profile.subjectName,
        externalRefId=profile.externalRefId,
        userId=profile.userId,
        status=profile.status,
        summary=profile.summary,
        traits=trait_items,
        narratives=narratives,
        createdAt=profile.createdAt,
        updatedAt=profile.updatedAt,
    )


async def get_profile_raw_data(profile_id: str) -> List[ScrapedDataItem]:
    profile = await Profile.get(PydanticObjectId(profile_id))
    if not profile:
        raise ValueError("Profile not found")

    items = await ScrapedData.find(ScrapedData.profile.id == profile.id).to_list()
    return [
        ScrapedDataItem(
            id=str(item.id),
            platform=item.platform,
            url=item.url,
            rawContent=item.rawContent,
            metadata=item.metadata,
            scrapedAt=item.scrapedAt,
            scrapeStatus=item.scrapeStatus,
            errorMessage=item.errorMessage,
        )
        for item in items
    ]


async def list_profiles(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProfileStatus] = None,
) -> List[ProfileListItem]:
    """List all profiles with optional filtering."""
    query = {}
    if status:
        query["status"] = status

    profiles = await Profile.find(query).skip(skip).limit(limit).sort(-Profile.createdAt).to_list()

    result = []
    for profile in profiles:
        traits = await ProfileTrait.find(ProfileTrait.profile.id == profile.id).to_list()
        overview: List[TraitOverviewItem] = []
        if traits:
            by_type = {}
            for t in traits:
                by_type.setdefault(t.traitType, []).append(t.score)
            for trait_type, scores in by_type.items():
                avg = sum(scores) / len(scores)
                overview.append(TraitOverviewItem(traitType=trait_type, averageScore=avg))

        result.append(
            ProfileListItem(
                id=str(profile.id),
                subjectName=profile.subjectName,
                externalRefId=profile.externalRefId,
                status=profile.status,
                traitsOverview=overview,
                errorMessage=profile.errorMessage,
                createdAt=profile.createdAt,
                updatedAt=profile.updatedAt,
            )
        )

    return result
