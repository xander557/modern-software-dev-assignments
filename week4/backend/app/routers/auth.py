from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import UserCreate, UserRead
from ..services.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user_by_username,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Register a new user."""
    # Check if username already exists
    existing_user = get_user_by_username(db, username=payload.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    hashed_password = get_password_hash(payload.password)
    user = User(username=payload.username, hashed_password=hashed_password)
    db.add(user)
    db.flush()
    db.refresh(user)
    return UserRead.model_validate(user)


@router.post("/login")
def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """Login with username and password, returns JWT token in cookie."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )

    return {"message": "Login successful", "username": user.username}


@router.post("/logout")
def logout(response: Response):
    """Logout by clearing the authentication cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserRead:
    """Get current authenticated user information."""
    return UserRead.model_validate(current_user)
