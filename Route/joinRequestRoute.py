from typing import Optional, List

from beanie import PydanticObjectId
from fastapi import HTTPException
from fastapi.routing import APIRouter

from Controller.joinRequestController import JoinRequestController
from Model.joinRequestModel import JoinRequest

joinRequestRoute = APIRouter(tags=["Join Request Route"])
# API to get many join requests
@joinRequestRoute.get("/join-requests", response_model=List[JoinRequest])
async def get_many_join_requests(libraryID: Optional[PydanticObjectId] = None, userID: Optional[PydanticObjectId] = None):
    return await JoinRequestController.get_join_requests(libraryID=libraryID, userID=userID)

# API to get one join request by ID
@joinRequestRoute.get("/join-request/{id}", response_model=JoinRequest)
async def get_one_join_request(id: PydanticObjectId):
    join_request = await JoinRequestController.get_join_request(id=id)
    if join_request is None:
        raise HTTPException(status_code=404, detail="Join Request not found")
    return join_request

# API to create a new join request
@joinRequestRoute.post("/join-request", response_model=dict)
async def create_join_request(body: JoinRequest = JoinRequest):
    return await JoinRequestController.create_join_request(body=body)

# API to delete a join request by ID
@joinRequestRoute.delete("/join-request/{id}", response_model=dict)
async def delete_join_request(id: PydanticObjectId):
    response = await JoinRequestController.delete_join_request(id=id)
    if response["response"] == "Join Request not found":
        raise HTTPException(status_code=404, detail="Join Request not found")
    return response
