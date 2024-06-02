from typing import Optional
from datetime import date
from beanie import Document, PydanticObjectId
from pydantic import Field


class JoinRequest(Document):
    userID: Optional[PydanticObjectId] = None,
    libraryID: Optional[PydanticObjectId] = None,
    dateCreated: Optional[date] = Field(default=None)

    class Config:
        example = {
            "userID":"66021d1fe7f2ad7b89a7cda8",
            "libraryID":"66021d1fe7f2ad7b89a7cda8",
        }
