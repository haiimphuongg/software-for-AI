import datetime
import hashlib

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Any

from pydantic import EmailStr

from Controller.authController import AuthController
from Controller.bookController import BookController
from Controller.borrowController import BorrowController
from Controller.joinRequestController import JoinRequestController
from Controller.libraryController import LibraryController
from Controller.notificationController import NotificationController
from Model.bookModel import BookUpdate
from Model.borrowModel import Borrow
from Model.joinRequestModel import JoinRequest
from Model.libraryModel import LibraryReturn
from Model.notificationModel import Notification, NotificationUpdate
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
        username: str = None,
        email: Optional[EmailStr] = None,
        get_all: Optional[bool] = False

) -> Any:
    AuthController.check_role(decoded_token, ["admin"])
    library_objectID: List[PydanticObjectId] = None
    if libraryID is not None:
        library_objectID = []
        for id in range(len(libraryID)):
            library_objectID.append(PydanticObjectId(libraryID[id]))

    list_user = await UserController.get_all_user(limit=limit,  page=page, sort_by=sort_by,
                                                  role= role, libraryID=library_objectID,
                                                  get_all=get_all, username= username,
                                                  email= email)
    for user in list_user:
        if user.role == "admin":
            list_user.remove(user)
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
    print(user.dict)
    print(body.dict)
    for attr in vars(body):
        if getattr(user, attr) != getattr(body, attr) and \
           getattr(body, attr) is not None and \
           getattr(body, attr) != []:
            if (attr == "status") or \
               (attr == "role") or \
               (attr == "listOfLib" and getattr(body, attr) != []) or \
               (attr == "password" and hashlib.md5(getattr(body, attr).encode()).hexdigest() != user.password):
                raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
            setattr(user, attr, getattr(body, attr))

    user_update = await UserController.update_user(id=userID, body=convert_model(user, UserUpdate), encoded=True)
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


@userRoute.get("/libraries/request", response_model=List[LibraryReturn],
               summary="GET all requests that the user has enrolled (for LOGGED IN USER")
async def list_requests(
        decoded_token = Depends(AuthController())
) -> List[LibraryReturn]:
    user_id = decoded_token["id"]
    list_requests = await JoinRequestController.get_join_requests(userID= PydanticObjectId(user_id))

    list_libraries_return = []
    for request in list_requests:
        list_libraries_return.append(convert_model(await LibraryController.get_library(PydanticObjectId(request.libraryID)),LibraryReturn))
    return list_libraries_return


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

    username = (await UserController.get_user(id=userID)).username
    notification = NotificationController.create_notification_model(
        status=False,
        subject="join request",
        source=PydanticObjectId(userID),
        target=PydanticObjectId(body.libraryID),
        createDate=datetime.datetime.today().date(),
        content=f"{username} want to join your library.",
        receive_role="library"
    )
    await NotificationController.create_notification(notification)
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

    username = (await UserController.get_user(id=body.userID)).username
    notification = NotificationController.create_notification_model(
        status=False,
        subject="borrow request",
        source=PydanticObjectId(body.userID),
        target=PydanticObjectId(body.libraryID),
        createDate=datetime.datetime.today().date(),
        content=f"{username} want to borrow \"{book.title}\".",
        receive_role="library"
    )
    await NotificationController.create_notification(notification)
    return response



@userRoute.get("/notifications", response_model= List[Notification],
               summary="GET all notifications of user (FOR LOGGED IN USER)")
async def get_notifications(
        decoded_token = Depends(AuthController()),
        subject: str = None,
        source: str = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "_id",
        status: bool = None

) -> List[Notification]:
    user_id = decoded_token["id"]
    username = (await UserController.get_user(user_id)).id
    notifications = await NotificationController.get_notifications(target=username, source=source,
                                                                   page=page, limit=limit, sort_by=sort_by,
                                                                   status=status, subject=subject)
    return notifications



@userRoute.get("/notifications/{id}", response_model=Notification,
               summary="GET notification of user (FOR LOGGED IN USER)")
async def get_notification(
        decoded_token = Depends(AuthController()),
        id: PydanticObjectId = None,

) -> Notification:
    user_id = decoded_token["id"]

    notification = await NotificationController.get_notification(id=id)
    if str(user_id) != str(notification.target):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    return notification


@userRoute.put("/notifications/{id}", response_model=NotificationUpdate,
               summary="UPDATE notification of user (FOR LOGGED IN USER)")
async def update_notification(
        decoded_token = Depends(AuthController()),
        id: PydanticObjectId = None,
        body: NotificationUpdate = None
) -> NotificationUpdate:
    user_id = decoded_token["id"]
    notification_update = await NotificationController.update_notification(id=id, body=body, target=user_id)
    return notification_update


@userRoute.get("/{id}", response_model=User)
async def get_user_by_id(
        id: PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> User:
    AuthController.check_role(decoded_token, ["admin"])
    user = await UserController.get_user(id)
    return user


@userRoute.post("",
                summary="CREATE a new USER with all roles (FOR ONLY ADMIN)")
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


@userRoute.put("/{id}", response_model=User,
               summary="UPDATE user info (FOR ADMIN)")
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


@userRoute.delete("/{id}", response_model=dict,
                  summary="DELETE a user (FOR ADMIN)")
async def delete_user(
        id:PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    response = await UserController.delete_user(id)
    return response

