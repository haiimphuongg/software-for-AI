from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Any

import Utils.Utils
from Controller.borrowController import BorrowController
from Controller.userController import UserController
from Model.bookModel import Book, book_to_book_update
from Model.borrowModel import Borrow, BorrowUpdate
from Model.joinRequestModel import JoinRequest
from Model.libraryModel import Library, LibraryUpdate
from Model.userModel import User, UserUpdate
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
async def get_books(decoded_token = Depends(AuthController())) -> List[Book]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    books = await BookController.get_books(libraryID=PydanticObjectId(library_id))
    return books


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


@libraryRoute.get("/members", response_model=List[User],
                  summary="GET new members (for LOGGED IN LIBRARY)")
async def get_library_members(
        decoded_token = Depends(AuthController()),
) -> List[User]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    users = await UserController.get_all_user(libraryID=[PydanticObjectId(library_id)])
    return users


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

    if accept == True:
        user = await UserController.get_user(PydanticObjectId(request.userID))
        user.listOfLib.append(library_id)
        user = convert_model(user, UserUpdate)
        await UserController.update_user(id=PydanticObjectId(request.userID), body=user)

    await JoinRequestController.delete_join_request(id=id)
    return {"message": "Request has been handled"}


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
async def get_books(id: PydanticObjectId) -> List[Book]:
    books = await BookController.get_books(libraryID=id)
    return books



