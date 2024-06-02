from fastapi import HTTPException, Query
from typing import Any, List, Optional
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

        new_user = User(
            username=user.username,
            password=hashed_password,
            dateOfBirth=user.dateOfBirth,
            role=user.role,
            listOfLib=user.listOfLib,
            address=user.address,
            email=user.email,
            status=True,
            avatarUrl=user.avatarUrl
        )
        await user_database.create(new_user)
        return {"message": "User register successfully"}

    @staticmethod
    async def update_user(body: UserUpdate, id: PydanticObjectId) -> User:
        user = await user_database.get_one(id)
        if not user:
            raise HTTPException(status_code=404, detail="Can't Find User")

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
            libraryID: Optional[List[PydanticObjectId]] = None
    ) -> List[User]:
        query = {}

        if role is not None:
            query.update({"role": role})
        if libraryID is not None:
            query.update({"listOfLib": {"$all": libraryID}})
        user = await user_database.get_all(limit=limit, page=page, sort_by=sort_by, query=query)
        if user is None:
            raise HTTPException(status_code=500, detail="Something went wrong")
        return user

    @staticmethod
    async def delete_user(id: PydanticObjectId) -> dict:
        is_delete = await user_database.delete(id)
        if not is_delete:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User is deleted successfully"}