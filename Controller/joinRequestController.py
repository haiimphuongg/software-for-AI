from typing import Optional, List

from beanie import PydanticObjectId
from fastapi import HTTPException

from Database.connection import Database
from Model.joinRequestModel import JoinRequest

joinRequestDatabase = Database(JoinRequest)

class JoinRequestController:

    @staticmethod
    async def get_join_requests(
            libraryID: Optional[PydanticObjectId] = None,
            userID: Optional[PydanticObjectId] = None,
            get_all: Optional[bool] = False
    ) -> List[JoinRequest]:
        query = {}
        if libraryID is not None:
            query.update({"libraryID": libraryID})
        if userID is not None:
            query.update({"userID": userID})
        join_requests = await joinRequestDatabase.get_all(query=query, get_all=get_all)
        return join_requests

    @staticmethod
    async def get_join_request(
            id: Optional[PydanticObjectId]
    ) -> JoinRequest:
        request = await joinRequestDatabase.get_one(id=id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        return request

    @staticmethod
    async def create_join_request(
            body: JoinRequest
    ) -> dict:
        response = await joinRequestDatabase.create(body)
        return {"response": "Join Request created successfully"}

    @staticmethod
    async def delete_join_request(
            id: Optional[PydanticObjectId]
    ) -> dict:
        response = await joinRequestDatabase.delete(id)
        if response:
            return {"response": "Join Request deleted successfully"}
