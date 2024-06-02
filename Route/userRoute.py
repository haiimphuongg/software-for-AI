import datetime
import hashlib

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Any

from Controller.authController import AuthController
from Controller.bookController import BookController
from Controller.borrowController import BorrowController
from Controller.joinRequestController import JoinRequestController
from Controller.libraryController import LibraryController
from Model.bookModel import BookUpdate
from Model.borrowModel import Borrow
from Model.joinRequestModel import JoinRequest
from Model.libraryModel import LibraryReturn
from Model.userModel import User, UserUpdate, UserReturn
from Controller.userController import UserController
from beanie import PydanticObjectId

from Utils.Utils import convert_model

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
        decoded_token = Depends(AuthController()),
        get_all: Optional[bool] = False

) -> Any:
    AuthController.check_role(decoded_token, ["admin"])
    library_objectID: List[PydanticObjectId] = None
    if libraryID is not None:
        library_objectID = []
        for id in range(len(libraryID)):
            library_objectID.append(PydanticObjectId(libraryID[id]))

    list_user = await UserController.get_all_user(limit=limit,  page=page, sort_by=sort_by,
                                                role= role, libraryID=library_objectID, get_all=get_all)
    return list_user


@userRoute.get("/info", response_model=UserReturn,
               summary="Get information of an user (for LOGGED IN USER)")
async def get_user_info(
        decoded_token = Depends(AuthController())
) -> UserReturn:
    userID = decoded_token["id"]
    user = await UserController.get_user(userID)
    return convert_model(user, UserReturn)


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
        or str(body.listOfLib) != str(user.listOfLib)
        or str(hashlib.md5(body.password.encode()).hexdigest()) != str(user.password)):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    user_update = await UserController.update_user(id=userID, body=body)
    return convert_model(user_update, UserReturn)


@userRoute.put("/info/password", response_model=dict,
               summary="Change password (for LOGGED IN USER)")
async def change_password(
        decoded_token = Depends(AuthController()),
        old_password: str = None,
        new_password: str = None,
        confirm_password: str = None,
) -> dict:
    userID = decoded_token["id"]
    user = await UserController.get_user(userID)
    if hashlib.md5(old_password.encode()).hexdigest() != user.password:
        return {"message": "Wrong password"}
    if confirm_password != new_password:
        return {"message": "New password does not match"}
    user.password = new_password
    await UserController.update_user(id=userID, body=convert_model(user, UserUpdate))
    return {"message": "Password changed successfully"}


@userRoute.get("/libraries", response_model=List[LibraryReturn],
               summary="GET all libraries that the user has enrolled (for LOGGED IN USER)")
async def list_libraries(
        decoded_token = Depends(AuthController()),
) -> List[LibraryReturn]:
    userID = decoded_token["id"]
    user = await UserController.get_user(userID)
    list_libraries = []
    for library_id in user.listOfLib:
        list_libraries.append(convert_model(await LibraryController.get_library(library_id), LibraryReturn))
    return list_libraries


@userRoute.post("/libraries/request", response_model=dict,
                summary="POST a join request to a library (for LOGGED IN USER)")
async def create_join_request(
        decoded_token = Depends(AuthController()),
        body: JoinRequest = None,
) -> dict:
    AuthController.check_role(decoded_token, ["user"])
    userID = decoded_token["id"]
    body.userID = PydanticObjectId(userID)
    body.dateCreated = datetime.datetime.today().date()
    response = await JoinRequestController.create_join_request(body=body)
    return response


@userRoute.get("/borrows", response_model=List[Borrow],
               summary="GET all borrows of an user (for LOGGED IN USER)")
async def get_borrows(
        decoded_token = Depends(AuthController()),
        status: Optional[str] = None
) -> List[Borrow]:
    userID = decoded_token["id"]
    list_borrows = await BorrowController.get_borrows(userID=PydanticObjectId(userID), status= status)
    return list_borrows


@userRoute.post("/borrows", response_model=dict,
                summary="POST a borrow of an user (for LOGGED IN USER)")
async def create_borrow(
        body: Borrow,
        decoded_token = Depends(AuthController()),

) -> dict:
    body.userID = PydanticObjectId(decoded_token["id"])
    book = await BookController.get_book(body.bookID)
    body.libraryID = PydanticObjectId(book.libraryID)
    library = await LibraryController.get_library(body.libraryID)

    body.returnDate = body.borrowDate + datetime.timedelta(days=library.maxBorrowDays)
    if book.currentNum <= 0:
        raise HTTPException(status_code=400, detail="No book in library")

    book_update = convert_model(book, BookUpdate)
    book_update.currentNum = book_update.currentNum - 1
    await BookController.update_book(id=book.id, body=book_update)
    response = await BorrowController.create_borrow(body=body)
    return response




@userRoute.get("/{id}", response_model=User)
async def get_user_by_id(
        id: PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> User:
    AuthController.check_role(decoded_token, ["admin"])
    user = await UserController.get_user(id)
    return user


@userRoute.post("")
async def register(
        body: User,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    try:
        new_user = await UserController.register(body)
        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@userRoute.put("/{id}", response_model=User)
async def update_user(
        id: PydanticObjectId,
        body: UserUpdate,
        decoded_token = Depends(AuthController())
) -> User:
    AuthController.check_role(decoded_token, ["admin"])
    try:
        user = await UserController.update_user(id= id, body= body)
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@userRoute.delete("/{id}", response_model=dict)
async def delete_user(
        id:PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    user = await UserController.delete_user(id)
    return user