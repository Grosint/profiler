from fastapi import APIRouter

from app.schemas.response import APIResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse[dict])
async def health() -> APIResponse[dict]:
    return APIResponse(success=True, data={"status": "ok"})


@router.get("/health/db", response_model=APIResponse[dict])
async def health_db() -> APIResponse[dict]:
    # For now we just return ok; later we can add a real ping to Mongo.
    return APIResponse(success=True, data={"status": "ok"})


@router.get("/health/queue", response_model=APIResponse[dict])
async def health_queue() -> APIResponse[dict]:
    # For now we just return ok; later we can add a real ping to Redis/Celery.
    return APIResponse(success=True, data={"status": "ok"})
