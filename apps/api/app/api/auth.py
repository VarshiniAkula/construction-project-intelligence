import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from supabase._async.client import AsyncClient

from app.deps import get_sb, get_current_user, _single
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.jwt import verify_password, hash_password, create_access_token, create_refresh_token
from app.services.audit_service import log_action

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, response: Response, sb: AsyncClient = Depends(get_sb)):
    # Check if email already taken
    existing = await sb.table("users").select("id").eq("email", body.email).execute()
    if existing.data and len(existing.data) > 0:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": body.email,
            "password_hash": hash_password(body.password),
            "full_name": body.full_name,
            "company_name": body.company_name or "",
            "is_active": True,
            "is_superadmin": False,
        }
        await sb.table("users").insert(user_data).execute()

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        response.set_cookie(
            key="access_token", value=access_token,
            httponly=True, samesite="lax", max_age=43200,
        )
        response.set_cookie(
            key="refresh_token", value=refresh_token,
            httponly=True, samesite="lax", max_age=604800,
        )

        await log_action(sb, "auth.register", user_id=user_id)
        return TokenResponse(access_token=access_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, sb: AsyncClient = Depends(get_sb)):
    result = await sb.table("users").select("*").eq("email", body.email).maybe_single().execute()
    user = _single(result)
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
