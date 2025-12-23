from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..models import ActionItem, User
from ..schemas import ActionItemCreate, ActionItemRead

router = APIRouter(prefix="/action-items", tags=["action_items"])


@router.get("/", response_model=list[ActionItemRead])
def list_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ActionItemRead]:
    """List all action items for the current user."""
    rows = (
        db.execute(select(ActionItem).where(ActionItem.user_id == current_user.id)).scalars().all()
    )
    return [ActionItemRead.model_validate(row) for row in rows]


@router.post("/", response_model=ActionItemRead, status_code=201)
def create_item(
    payload: ActionItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActionItemRead:
    """Create a new action item for the current user."""
    item = ActionItem(
        description=payload.description,
        completed=False,
        user_id=current_user.id,
    )
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/complete", response_model=ActionItemRead)
def complete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActionItemRead:
    """Mark an action item as complete for the current user."""
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")

    # Ensure user owns this item
    if item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Action item not found")

    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)
