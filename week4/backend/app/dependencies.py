from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .services.auth import ALGORITHM, SECRET_KEY, get_user_by_username


async def get_current_user(
    access_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token in cookie.
    Raises HTTPException if token is invalid or missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not access_token:
        raise credentials_exception

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception

    return user
