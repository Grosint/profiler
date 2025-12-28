from typing import Optional

from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundException
from app.models.post import PostStatus
from app.schemas.post import (
    CreatePostAnalysisRequest,
    PostStatusResponse,
    PostListItem,
)
from app.schemas.response import APIResponse
from app.services.post_analysis_service import (
    create_post_analysis_job,
    get_post_status,
    list_posts,
)
from app.tasks.post_tasks import run_post_analysis_pipeline

router = APIRouter()


@router.get("/posts", response_model=APIResponse[list[PostListItem]])
async def list_posts_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[PostStatus] = Query(None),
) -> APIResponse[list[PostListItem]]:
    """List all post analyses with optional filtering."""
    posts = await list_posts(skip=skip, limit=limit, status=status)
    return APIResponse(success=True, data=posts)


@router.post("/posts", response_model=APIResponse[PostStatusResponse])
async def create_post_analysis(payload: CreatePostAnalysisRequest) -> APIResponse[PostStatusResponse]:
    """Create a new post analysis job."""
    post = await create_post_analysis_job(payload)
    # Enqueue async pipeline
    run_post_analysis_pipeline.delay(str(post.id))
    status = await get_post_status(str(post.id))
    return APIResponse(success=True, data=status)


@router.get("/posts/{post_id}", response_model=APIResponse[PostStatusResponse])
async def get_post(post_id: str) -> APIResponse[PostStatusResponse]:
    """Get post analysis status."""
    try:
        status = await get_post_status(post_id)
    except ValueError:
        raise NotFoundException("Post not found")
    return APIResponse(success=True, data=status)
