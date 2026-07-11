from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.jwt import create_access_token, require_user
from app.config.settings import Settings, get_settings
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, settings: Settings = Depends(get_settings)) -> LoginResponse:
    if payload.email != settings.demo_admin_email or payload.password != settings.demo_admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=payload.email, role="admin", settings=settings)
    return LoginResponse(
        access_token=token,
        role="admin",
        user={"email": payload.email, "name": "Demo Admin", "tenant": "Local Development"},
    )


@router.get("/me")
async def me(user: dict = Depends(require_user)) -> dict:
    return {"user": user}
