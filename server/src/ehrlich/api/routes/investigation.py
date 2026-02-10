from fastapi import APIRouter

router = APIRouter(tags=["investigation"])


@router.post("/investigate")
async def start_investigation() -> dict[str, str]:
    return {"status": "not_implemented"}
