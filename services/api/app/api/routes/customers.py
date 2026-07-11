from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_customers() -> dict:
    return {"items": [], "next_cursor": None}
