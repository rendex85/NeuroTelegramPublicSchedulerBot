from enum import Enum

from sqlmodel import SQLModel, Field


class ImgType(Enum):
    anime = "anime"
    meme = "meme"


class Post(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    file_id: str
    img_type: str
    spoiler: bool = Field(default=False)
    caption: str | None


