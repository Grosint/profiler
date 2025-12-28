from fastapi import APIRouter, Response

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


@router.options("/health/cors-test")
async def cors_test_options() -> Response:
    """Test endpoint for CORS preflight."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        },
    )


@router.get("/health/cors-test")
async def cors_test() -> dict:
    """Test endpoint to verify CORS is working."""
    return {"cors": "working", "origin_allowed": "*"}
