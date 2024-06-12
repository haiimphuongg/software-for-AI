import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Any

import Utils.Utils
from Controller.borrowController import BorrowController
from Controller.notificationController import NotificationController
from Controller.userController import UserController
from Model.bookModel import Book, book_to_book_update
from Model.borrowModel import Borrow, BorrowUpdate
from Model.joinRequestModel import JoinRequest
from Model.libraryModel import Library, LibraryUpdate
from Model.notificationModel import Notification, NotificationUpdate
from Model.userModel import User, UserUpdate, UserReturn
from Controller.libraryController import LibraryController
from beanie import PydanticObjectId
from Controller.bookController import BookController
from Controller.authController import AuthController
from Controller.joinRequestController import JoinRequestController
from Utils.Utils import *


libraryRoute = APIRouter(tags=["Library"])


@libraryRoute.get("/", response_model=List[Library],
                  summary= "GET all libraries (for ALL ROLES)")
async def get_all_libraries(
        limit: Optional[int] = 10,
        page: Optional[int] = 1,
        sort_by: Optional[str] = "_id",
        name: Optional[str] = None,
        slug: Optional[str] = "",
) -> List[Library]:
    libraries = await LibraryController.get_libraries(limit=limit, page=page, sort_by=sort_by, slug= slug, name= name)
    return libraries


@libraryRoute.post("/new", response_model=dict,
                   summary="POST a new library (for ADMIN)")
async def create_library(body: Library, decoded_token = Depends(AuthController())) -> dict:
    AuthController.check_role(decoded_token=decoded_token, roles=["admin"])
    library = await LibraryController.create_library(body=body)
    return library


@libraryRoute.get("/info",
                  summary="Get info (for LOGGED IN LIBRARY)")
async def get(decoded_token: Any = Depends(AuthController())):
    manager_id = decoded_token["id"]
    library = await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id))
    return library


@libraryRoute.put("/info", response_model=Library,
                  summary="PUT the info (for LOGGED IN LIBRARY)")
async def update_library_info(
        body:LibraryUpdate,
        decoded_token = Depends(AuthController())
) -> Library:
    manager_id = decoded_token["id"]
    library = await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id))
    if len(library) == 0:
        raise HTTPException(status_code=404,detail="Library not found")

    id = library[0].id
    library = await LibraryController.update_library(id=id, body=body)
    return library


@libraryRoute.get("/books", response_model=List[Book],
                  summary="GET all books (for LOGGED IN LIBRARY)")
async def get_books(
        decoded_token = Depends(AuthController()),
        page: Optional[int] = 1,
        limit: Optional[int] = 10,
        sort_by: Optional[str] = "_id",
        slug: Optional[str] = None,
        genres: Optional[List[str]] = Query(None, alias="genres"),
        publisher: Optional[str] = Query(None, alias="publisher"),
        language: Optional[str] = Query(None, alias="language"),
        get_all: Optional[bool] = False,
        author: Optional[List[str]] = Query(None, alias="author"),
        series: Optional[List[str]] = Query(None, alias="series")
) -> List[Book]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    books = await BookController.get_books(libraryID=PydanticObjectId(library_id), page=page,
                                           limit=limit, sort_by=sort_by, slug=slug, genres=genres,
                                           publisher=publisher, language=language, get_all=get_all,
                                           author=author, series=series)
    return books


@libraryRoute.post("/books", response_model=dict,
                   summary="POST a new book (for LOGGED IN LIBRARY)")
async def create_book(
        body: Book,
        decoded_token= Depends(AuthController()),

) -> dict:
    manager_id = decoded_token["id"]
    library = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0]
    library_id = library.id
    library_name = library.name

    body.libraryID = library_id
    body.libraryName = library_name
    body.avgRating = 0
    body.numOfRating = 0

    response = await BookController.create_book(book=body)
    return response


@libraryRoute.delete("/books/{bookID}", response_model=dict,
                     summary="DELETE a book (for LOGGED IN LIBRARY")
async def delete_book(
        deleted_book=Depends(AuthController()),
        id: PydanticObjectId = None,
) -> dict:
    manager_id = deleted_book["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    book = await BookController.get_book(id=id)

    if book.libraryID != library_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this book")

    response = await BookController.delete_book(id=id)
    return response




@libraryRoute.get("/borrows", response_model=List[Borrow],
                  summary="GET all borrows (for LOGGED IN LIBRARY)")
async def get_borrows_in_library(
        decoded_token = Depends(AuthController())
) -> List[Borrow]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    borrows = await BorrowController.get_borrows(libraryID=library_id)
    return borrows


@libraryRoute.post("/borrows", response_model=dict,
                   summary="POST new borrows (for LOGGED IN LIBRARY)")
async def create_borrows_in_library(
        body: Borrow,
        decoded_token = Depends(AuthController()),
) -> dict:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    if str(library_id) != str(body.libraryID):
        raise HTTPException(status_code=403,detail="You don not have permission to perform this action")

    book = await BookController.get_book(body.bookID)
    if book.currentNum <= 0:
        raise HTTPException(status_code=400, detail="No book in library")

    book_update = book_to_book_update(book)
    book_update.currentNum = book_update.currentNum - 1
    await BookController.update_book(id=book.id, body=book_update)
    response = await BorrowController.create_borrow(body=body)
    return response


@libraryRoute.get("/members", response_model=List[UserReturn],
                  summary="GET new members (for LOGGED IN LIBRARY)")
async def get_library_members(
        decoded_token = Depends(AuthController()),
) -> List[User]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    users = await UserController.get_all_user(libraryID=[PydanticObjectId(library_id)])
    for i in range(len(users)):
        users[i] = convert_model(users[i], UserReturn)
    return users


@libraryRoute.put("/members", response_model=dict,
                  summary="ADD new members (for LOGGED IN LIBRARY)")
async def add_library_member(
        decoded_token = Depends(AuthController()),
        member_id: PydanticObjectId = None
) -> dict:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    user = await UserController.get_user(PydanticObjectId(member_id))
    user.listOfLib.append(library_id)
    user = convert_model(user, UserUpdate)
    print(user.dict())
    await UserController.update_user(id=PydanticObjectId(member_id), body=user, encoded=True)
    return {"message": "Request has been handled"}


@libraryRoute.get("/members/requests", response_model=List[JoinRequest],
                  summary="GET all join requests (for LOGGED IN LIBRARY)")
async def get_join_requests(
        decoded_token = Depends(AuthController())
) -> List[JoinRequest]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    print("Library ID:", library_id)
    join_requests = await JoinRequestController.get_join_requests(libraryID=PydanticObjectId(library_id))
    return join_requests

@libraryRoute.delete("/members/requests/{id}", response_model=dict,
                     summary="Accept or Deny a request from user (for LOGGED IN LIBRARY)")
async def handle_request(
        id: PydanticObjectId,
        accept: bool = True,
        decoded_token = Depends(AuthController()),

) -> dict:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id

    request = await JoinRequestController.get_join_request(id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if str(request.libraryID) != str(library_id):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    action = "denied"
    if accept == True:
        action = "accepted"
        user = await UserController.get_user(PydanticObjectId(request.userID))
        user.listOfLib.append(library_id)
        user = convert_model(user, UserUpdate)
        print(user.dict())
        await UserController.update_user(id=PydanticObjectId(request.userID), body=user, encoded=True)

    await JoinRequestController.delete_join_request(id=id)

    library_name = (await LibraryController.get_library(id=request.libraryID)).name
    notification = NotificationController.create_notification_model(
        status=False,
        subject="borrow request",
        source=PydanticObjectId(request.libraryID),
        target=PydanticObjectId(request.userID),
        createDate=datetime.datetime.today().date(),
        content=f"{library_name} {action} your request to join.",
        receive_role="user"
    )
    await NotificationController.create_notification(notification)
    return {"message": "Request has been handled"}


@libraryRoute.get("/notifications", response_model=List[Notification],
                  summary="GET all notifications of a library (for LOGGED IN LIBRARY)")
async def get_notifications(
        decoded_token = Depends(AuthController()),
        subject: str = None,
        source: str = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "_id",
        status: bool = None

) -> List[Notification]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    notifications = await NotificationController.get_notifications(target=library_id, source=source,
                                                                   page=page, limit=limit, sort_by=sort_by,
                                                                   status=status, subject=subject)
    return notifications


@libraryRoute.get("/notifications/{id}", response_model=Notification,
               summary="GET notification of library (FOR LOGGED IN LIBRARY)")
async def get_notification(
        decoded_token = Depends(AuthController()),
        id: PydanticObjectId = None,

) -> Notification:
    user_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(user_id)))[0].id

    notification = await NotificationController.get_notification(id=id)
    if str(library_id) != str(notification.target):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    return notification



@libraryRoute.put("/notifications/{id}", response_model=NotificationUpdate,
               summary="UPDATE notification of library (FOR LOGGED IN LIBRARY)")
async def update_notification(
        decoded_token = Depends(AuthController()),
        id: PydanticObjectId = None,
        body: NotificationUpdate = None
) -> NotificationUpdate:
    user_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(user_id)))[0].id
    notification_update = await NotificationController.update_notification(id=id, body=body, target=library_id)
    return notification_update


@libraryRoute.get("/{id}", response_model=Library,
                  summary="GET a library's information (for ALL ROLES)")
async def get_library(id: PydanticObjectId) -> Library:
    library = await LibraryController.get_library(id)
    return library


@libraryRoute.put("/{id}", response_model=Library,
                  summary="PUT a library's information (for ADMIN)")
async def update_library(
        id: PydanticObjectId,
        body:LibraryUpdate,
        decoded_token = Depends(AuthController())
) -> Library:
    AuthController.check_role(decoded_token=decoded_token, roles=["admin"])
    library = await LibraryController.update_library(id=id, body=body)
    return library


@libraryRoute.delete("/{id}", response_model=dict,
                     summary="DELETE a library information (for ADMIN)")
async def delete_library(id: PydanticObjectId, decoded_token = Depends(AuthController())) -> dict:
    AuthController.check_role(decoded_token=decoded_token, roles=["admin"])
    library = await LibraryController.delete_library(id=id)
    return library


@libraryRoute.put("/borrows/{id}", response_model=Borrow,
                  summary="PUT a library's information (for ADMIN)")
async def update_borrow(
        id: PydanticObjectId,
        body: BorrowUpdate,
        decoded_token = Depends(AuthController())
) -> Borrow:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    if str(library_id) != str(body.libraryID):
        raise HTTPException(status_code=403,detail="You don not have permission to perform this action")
    borrow = await BorrowController.update_borrow(body=body, borrowID=id)
    return borrow


@libraryRoute.get("/{id}/books", response_model=List[Book],
                  summary="GET all books in a library (for ALL ROLES)")
async def get_books(
        id: PydanticObjectId,
        page: Optional[int] = 1,
        limit: Optional[int] = 10,
        sort_by: Optional[str] = "_id",
        slug: Optional[str] = None,
        genres: Optional[List[str]] = Query(None, alias="genres"),
        publisher: Optional[str] = Query(None, alias="publisher"),
        language: Optional[str] = Query(None, alias="language"),
        get_all: Optional[bool] = False,
        author: Optional[List[str]] = Query(None, alias="author"),
        series: Optional[List[str]] = Query(None, alias="series")
) -> List[Book]:
    books = await BookController.get_books(libraryID=id, page=page, limit=limit,
                                           sort_by=sort_by, slug=slug, genres=genres,
                                           publisher=publisher, language=language,
                                           get_all=get_all, author=author, series=series)
    return books



