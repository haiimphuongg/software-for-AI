from pydantic import BaseModel, Field, EmailStr
from beanie import Document, PydanticObjectId
from typing import List, Optional
from datetime import date

from pymongo import IndexModel


class User(Document):
    username: str = Field(..., unique=True)
    password: str = Field(default=username)
    dateOfBirth: Optional[date] = Field(default=None)
    role: str = Field(default="user")
    listOfLib: Optional[List[PydanticObjectId]] = Field(default=[])
    address: Optional[str] = Field(default=None)
    status: Optional[bool] = Field(default=True)  # Assuming status is binary, using boolean for clarity
    email: EmailStr = Field(default=None, unique=True)
    avatarUrl: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "securepassword123",
                "dateOfBirth": "1990-01-01",
                "role": "user",
                "listOfLib": ["60d5ec59f2954c4d5c827d1b", "60d5ec59f2954c4d5c827d1c"],
                "address": "456 User Ave, Hometown",
                "status": True,
                "name": "Phuong"
            }
        }

    class Settings:
        collection = "User"
        indexes = [
            IndexModel([("username")], unique=True),
            IndexModel([("email")], unique=True)
        ]

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    dateOfBirth: Optional[date] = None
    role: Optional[str] = None
    listOfLib: Optional[List[PydanticObjectId]] = []
    address: Optional[str] = None
    status: Optional[bool] = None
    email: EmailStr = Field(default=None)
    avatarUrl: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    class Config:
        schema_extra = {
            "example": {
                "userName": "john_doe",
                "password": "securepassword123",
                "dateOfBirth": "1990-01-01",
                "role": "user",
                "listOfLib": ["60d5ec59f2954c4d5c827d1b", "60d5ec59f2954c4d5c827d1c"],
                "address": "456 User Ave, Hometown",
                "status": True
            }
        }

class UserReturn(BaseModel):
    id: PydanticObjectId = None
    username: Optional[str] = None
    dateOfBirth: Optional[date] = None
    role: Optional[str] = None
    listOfLib: Optional[List[PydanticObjectId]] = []
    address: Optional[str] = None
    status: Optional[bool] = True
    email: EmailStr = Field(default=None)
    avatarUrl: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    class Config:
        schema_extra = {
            "example": {
                "userName": "john_doe",
                "password": "securepassword123",
                "dateOfBirth": "1990-01-01",
                "role": "user",
                "listOfLib": ["60d5ec59f2954c4d5c827d1b", "60d5ec59f2954c4d5c827d1c"],
                "address": "456 User Ave, Hometown",
                "status": True
            }
        }
