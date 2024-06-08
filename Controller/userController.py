from fastapi import HTTPException, Query
from typing import Any, List, Optional

from pydantic import EmailStr

from Database.connection import Database
from beanie import init_beanie, PydanticObjectId
from Model.userModel import User
from Model.userModel import UserUpdate

import hashlib

user_database = Database(User)


class UserController:
    @staticmethod
    async def register(user: User) -> dict:
        # existing_user = await user_database.get_all({"username": user.username})
        # if existing_user:
        #    raise HTTPException(status_code=400, detail="Username already registered")

        hashed_password = hashlib.md5(user.password.encode()).hexdigest()
        print(user.dict)
        user.password = hashed_password
        await user_database.create(user)
        return {"message": "User register successfully"}

    @staticmethod
    async def update_user(body: UserUpdate, id: PydanticObjectId, encoded = False) -> User:
        user = await user_database.get_one(id)
        if not user:
            raise HTTPException(status_code=404, detail="Can't Find User")

        if not encoded:
            hashed_password = hashlib.md5(body.password.encode()).hexdigest()
            body.password = hashed_password
        user = await user_database.update(id=id, body=body)
        return user

    @staticmethod
    async def get_user(id: PydanticObjectId) -> User:
        user = await user_database.get_one(id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    async def get_all_user(
            limit: Optional[int] = 10,
            page: Optional[int] = 1,
            sort_by: Optional[str] = "username",
            role: Optional[str] = None,
            libraryID: Optional[List[PydanticObjectId]] = None,
            username:str = None,
            email: Optional[EmailStr] = None,
            get_all: Optional[bool] = False,

    ) -> List[User]:
        query = {}

        if role is not None:
            query.update({"role": role})
        if libraryID is not None:
            query.update({"listOfLib": {"$all": libraryID}})
        if username is not None:
            query.update({"username": username})
        if email is not None:
            query.update({"email": email})
        user = await user_database.get_all(limit=limit, page=page, sort_by=sort_by,
                                           query=query, get_all=get_all)
        if user is None:
            raise HTTPException(status_code=500, detail="Something went wrong")
        return user

    @staticmethod
    async def delete_user(id: PydanticObjectId) -> dict:
        is_delete = await user_database.delete(id)
        if not is_delete:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User is deleted successfully"}

