from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundException
from app.core.security import api_key_auth
from app.models.profile import ProfileStatus
from app.schemas.profile import (
    CreateProfileRequest,
    ProfileDetailsResponse,
    ProfileListItem,
    ProfileStatusResponse,
)
from app.schemas.response import APIResponse
from app.services.profiler_service import (
    create_profile_job,
    get_profile_details,
    get_profile_raw_data,
    get_profile_status,
    list_profiles,
)
from app.schemas.scraped_data import ScrapedDataItem
from app.tasks.profiler_tasks import run_profile_pipeline

router = APIRouter(dependencies=[Depends(api_key_auth)])


@router.get("/profiles", response_model=APIResponse[list[ProfileListItem]])
async def list_profiles_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ProfileStatus] = Query(None),
) -> APIResponse[list[ProfileListItem]]:
    """List all profiles with optional filtering."""
    profiles = await list_profiles(skip=skip, limit=limit, status=status)
    return APIResponse(success=True, data=profiles)


@router.post("/profiles", response_model=APIResponse[ProfileStatusResponse])
async def create_profile(payload: CreateProfileRequest) -> APIResponse[ProfileStatusResponse]:
    # TODO: URL validation and domain checks
    profile = await create_profile_job(payload)
    # #region agent log
    import json
    import os
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "profile-create", "hypothesisId": "A", "location": "profiler.py:create_profile", "message": "Profile created, enqueueing Celery task", "data": {"profile_id": str(profile.id), "urls": {"instagram": bool(payload.urls.instagramUrl), "facebook": bool(payload.urls.facebookUrl), "twitter": bool(payload.urls.twitterUrl), "linkedin": bool(payload.urls.linkedinUrl), "reddit": bool(payload.urls.redditUrl), "blogs": len(payload.urls.blogUrls or [])}}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    # Enqueue async pipeline
    task_result = run_profile_pipeline.delay(str(profile.id))
    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "profile-create", "hypothesisId": "A", "location": "profiler.py:create_profile", "message": "Celery task enqueued", "data": {"profile_id": str(profile.id), "task_id": str(task_result.id), "task_state": task_result.state}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    status = await get_profile_status(str(profile.id))
    return APIResponse(success=True, data=status)


@router.get("/profiles/{profile_id}", response_model=APIResponse[ProfileStatusResponse])
async def get_profile(profile_id: str) -> APIResponse[ProfileStatusResponse]:
    try:
        status = await get_profile_status(profile_id)
    except ValueError:
        raise NotFoundException("Profile not found")
    return APIResponse(success=True, data=status)


@router.get("/profiles/{profile_id}/details", response_model=APIResponse[ProfileDetailsResponse])
async def get_profile_details_endpoint(profile_id: str) -> APIResponse[ProfileDetailsResponse]:
    try:
        details = await get_profile_details(profile_id)
    except ValueError:
        raise NotFoundException("Profile not found")
    return APIResponse(success=True, data=details)


@router.get("/profiles/{profile_id}/raw-data", response_model=APIResponse[list[ScrapedDataItem]])
async def get_profile_raw_data_endpoint(profile_id: str) -> APIResponse[list[ScrapedDataItem]]:
    try:
        data = await get_profile_raw_data(profile_id)
    except ValueError:
        raise NotFoundException("Profile not found")
    return APIResponse(success=True, data=data)
