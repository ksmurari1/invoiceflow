"""Current user profile (business details shown on invoices)."""

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut)
async def read_me(user: User = Depends(get_current_user)) -> User:
    """Return the current user's profile and invoice defaults."""
    return user
