from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Any
from Model.bookModel import Book
from Model.libraryModel import Library, LibraryUpdate
from Controller.libraryController import LibraryController
from beanie import PydanticObjectId
from Controller.bookController import BookController
from Controller.authController import AuthController

libraryRoute =APIRouter(tags=["Library"])

@libraryRoute.get("/", response_model=List[Library])
async def get_all_libraries(
        limit: Optional[int] = 10,
        page: Optional[int] = 1,
        sort_by: Optional[str] = "_id",
        name: Optional[str] = None,
        slug: Optional[str] = "",
) -> List[Library]:
    libraries = await LibraryController.get_libraries(limit=limit, page=page, sort_by=sort_by, slug= slug, name= name)
    return libraries

@libraryRoute.get("/info")
async def get(decoded_token: Any = Depends(AuthController())):
    manager_id = decoded_token["id"]
    library = await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id))
    return library

@libraryRoute.get("/books", response_model=List[Book])
async def get_books(decoded_token = Depends(AuthController())) -> List[Book]:
    manager_id = decoded_token["id"]
    library_id = (await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id)))[0].id
    books = await BookController.get_books(libraryID=PydanticObjectId(library_id))
    return books

@libraryRoute.get("/{id}", response_model=Library)
async def get_library(id: PydanticObjectId) -> Library:
    library = await LibraryController.get_library(id)
    return library

@libraryRoute.post("/new", response_model=dict)
async def create_library(body: Library, decoded_token = Depends(AuthController())) -> dict:
    AuthController.check_role(decoded_token=decoded_token, roles=["admin"])
    library = await LibraryController.create_library(body=body)
    return library

@libraryRoute.put("/info", response_model=Library)
async def update_library_info(
        body:LibraryUpdate,
        decoded_token = Depends(AuthController())
) -> Library:
    manager_id = decoded_token["id"]
    library = await LibraryController.get_libraries(managerID=PydanticObjectId(manager_id))
    if len(library) == 0:
        raise HTTPException(status_code=404,detail="Library not found")

    id = library[0].id
    if (library[0].managerID != body.managerID
        or library[0].avgRating != body.avgRating
        or library[0].numOfRating != body.numOfRating):
        raise HTTPException(status_code=403,detail="You are not allowed to edit these fields")

    library = await LibraryController.update_library(id=id, body=body)
    return library

@libraryRoute.put("/{id}", response_model=Library)
async def update_library(
        id: PydanticObjectId,
        body:LibraryUpdate,
        decoded_token = Depends(AuthController())
) -> Library:
    AuthController.check_role(decoded_token=decoded_token, roles=["admin"])
    library = await LibraryController.update_library(id=id, body=body)
    return library

@libraryRoute.delete("/{id}", response_model=dict)
async def delete_library(id: PydanticObjectId, decoded_token = Depends(AuthController())) -> dict:
    AuthController.check_role(decoded_token=decoded_token, roles=["admin"])
    library = await LibraryController.delete_library(id=id)
    return library

@libraryRoute.get("/{id}/books", response_model=List[Book])
async def get_books(id: PydanticObjectId) -> List[Book]:
    books = await BookController.get_books(libraryID=id)
    return books



