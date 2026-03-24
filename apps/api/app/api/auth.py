from fastapi import APIRouter, Depends, HTTPException, Response, status
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.security.jwt import verify_password, create_access_token, create_refresh_token
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, sb: AsyncClient = Depends(get_sb)):
    result = await sb.table("users").select("*").eq("email", body.email).maybe_single().execute()
    user = result.data
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])

    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, samesite="lax", max_age=43200,
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, samesite="lax", max_age=604800,
    )

    await log_action(sb, "auth.login", user_id=user["id"])
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        company_name=user.company_name, is_active=user.is_active,
        is_superadmin=user.is_superadmin,
    )
