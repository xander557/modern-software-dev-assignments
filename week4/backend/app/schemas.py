from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    user_id: int

    class Config:
        from_attributes = True


class ActionItemCreate(BaseModel):
    description: str


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool
    user_id: int

    class Config:
        from_attributes = True
