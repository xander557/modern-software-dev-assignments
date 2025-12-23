from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..models import Note, User
from ..schemas import NoteCreate, NoteRead

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteRead])
def list_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NoteRead]:
    """List all notes for the current user."""
    rows = db.execute(select(Note).where(Note.user_id == current_user.id)).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteRead:
    """Create a new note for the current user."""
    note = Note(
        title=payload.title,
        content=payload.content,
        user_id=current_user.id,
    )
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/search/", response_model=list[NoteRead])
def search_notes(
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NoteRead]:
    """Search notes for the current user."""
    if not q:
        rows = db.execute(select(Note).where(Note.user_id == current_user.id)).scalars().all()
    else:
        rows = (
            db.execute(
                select(Note).where(
                    (Note.user_id == current_user.id)
                    & ((Note.title.contains(q)) | (Note.content.contains(q)))
                )
            )
            .scalars()
            .all()
        )
    return [NoteRead.model_validate(row) for row in rows]


@router.get("/{note_id}", response_model=NoteRead)
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteRead:
    """Get a specific note for the current user."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Ensure user owns this note
    if note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    return NoteRead.model_validate(note)
