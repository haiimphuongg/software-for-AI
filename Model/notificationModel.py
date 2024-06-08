from datetime import date
from typing import Literal

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class Notification(Document):
    source: PydanticObjectId = Field(...)
    target: PydanticObjectId = Field(...)
    subject: Literal["join request", "join response", "borrow request", "delete book"] = Field(default="join request")
    content: str = Field(default=None)
    receive_role: Literal["user", "admin", "library"] = Field(default=None)
    createDate: date = Field(default=None)
    status: bool = Field(default=None)

    class Config:
        schema_extra = {
            "example" : {
                "source": PydanticObjectId("665806e15e612a16a32d77f1"),
                "target": PydanticObjectId("665806e15e612a16a32d77f1"),
                "subject": "join request",
                "content": "join",
                "receive_role": "admin",
                "createDate": "2020-05-27",
                "status": True
            }
        }
class NotificationUpdate(BaseModel):
    status: bool = 1


