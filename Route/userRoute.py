from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Any

from Controller.authController import AuthController
from Model.userModel import User, UserUpdate, UserReturn
from Controller.userController import UserController
from beanie import PydanticObjectId

from Utils.Utils import model_to_model_update

userRoute = APIRouter(
    tags= ["User"]
)

@userRoute.get("", response_model=Any)
async def get_all_users(
        limit: Optional[int] = 10,
        page: Optional[int] = 1,
        sort_by: Optional[str] = "username",
        libraryID: Optional[List[str]] = Query(default=None, alias="libraryID"),
        role: Optional[str] = Query(None, alias="role"),

) -> Any:
    library_objectID: List[PydanticObjectId] = None
    if libraryID is not None:
        library_objectID = []
        for id in range(len(libraryID)):
            library_objectID.append(PydanticObjectId(libraryID[id]))

    list_user = await UserController.get_all_user(limit=limit,  page=page, sort_by=sort_by,
                                                role= role, libraryID=library_objectID)
    return list_user


@userRoute.get("/info", response_model=UserReturn,
               summary="Get information of an user (for LOGGED IN USER)")
async def get_user_info(
        decoded_token = Depends(AuthController())
) -> UserReturn:
    userID = decoded_token["id"]
    user = await UserController.get_user(userID)
    return model_to_model_update(user, UserReturn)


@userRoute.put("/info", response_model=UserReturn,
               summary="Update information of an user (for LOGGED IN USER)")
async def update_user_info(
        body: UserUpdate,
        decoded_token = Depends(AuthController()),
) -> UserReturn:
    userID = decoded_token["id"]
    user = await UserController.get_user(userID)
    if (body.role != user.role
        or body.status != user.status
        or body.listOfLib != user.listOfLib):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    user_update = await UserController.update_user(id=userID, body=body)
    return model_to_model_update(user_update, UserReturn)

@userRoute.get("/{id}", response_model=User)
async def get_user_by_id(id) -> User:
    user = await UserController.get_user(id)
    return user

@userRoute.post("")
async def register(body: User) -> dict:
    try:
        new_user = await UserController.register(body)
        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@userRoute.put("/{id}", response_model=User)
async def update_user(id: PydanticObjectId, body: UserUpdate) -> User:
    try:
        user = await UserController.update_user(id= id, body= body)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@userRoute.delete("/{id}", response_model=dict)
async def delete_user(id:PydanticObjectId) -> dict:
    user = await UserController.delete_user(id)
    return user