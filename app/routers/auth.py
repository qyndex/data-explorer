"""Authentication routes: sign-up, sign-in, profile."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.database import get_supabase_client
from app.models import (
    AuthResponse,
    ProfileResponse,
    SignInRequest,
    SignUpRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def sign_up(body: SignUpRequest):
    """Register a new user. The profile trigger auto-creates the profile row."""
    sb = get_supabase_client()
    try:
        result = sb.auth.sign_up(
            {
                "email": body.email,
                "password": body.password,
                "options": {"data": {"full_name": body.full_name}},
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    session = result.session
    user = result.user
    if session is None or user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sign-up failed — check email confirmation settings",
        )

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user_id=user.id,
        email=user.email or body.email,
    )


@router.post("/signin", response_model=AuthResponse)
async def sign_in(body: SignInRequest):
    """Authenticate with email + password and return JWT tokens."""
    sb = get_supabase_client()
    try:
        result = sb.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    session = result.session
    user = result.user
    if session is None or user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user_id=user.id,
        email=user.email or body.email,
    )


@router.post("/signout", status_code=204)
async def sign_out(_user_id: str = Depends(get_current_user_id)):
    """Sign out the current user (invalidates the session server-side)."""
    sb = get_supabase_client()
    try:
        sb.auth.sign_out()
    except Exception:
        pass  # Best-effort; token is already invalidated client-side


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user_id)):
    """Return the authenticated user's profile."""
    sb = get_supabase_client()
    result = (
        sb.table("profiles")
        .select("id, email, full_name, plan, created_at")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return ProfileResponse(**result.data)
