from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from Controller.authController import AuthController
from Model.bookModel import Book, BookUpdate
from Controller.bookController import BookController
from beanie import PydanticObjectId
bookRoute = APIRouter(
    tags= ["Book"]
)

@bookRoute.get("", response_model=List[Book])
async def get_all_books(
        limit: Optional[int] = 10,
        page: Optional[int] = 1,
        sort_by: Optional[str] = "_id",
        slug: Optional[str] = "",
        genres: Optional[List[str]] = Query(None, alias="genres"),
        publisher: Optional[str] = Query(None, alias="publisher"),
        language: Optional[str] = Query(None, alias="language"),
        author: Optional[List[str]] = Query(None, alias="author"),
        series: Optional[List[str]] = Query(None, alias="series"),
        get_all: Optional[bool] = False
) -> List[Book]:
    list_book = await BookController.get_books(limit=limit, page=page, sort_by=sort_by,
                                               slug= slug, genres=genres, publisher=publisher,
                                               language=language, author=author, series=series,
                                               get_all=get_all)
    return list_book

@bookRoute.get("/{id}", response_model=Book)
async def get_book_by_id(id) -> Book:
    book = await BookController.get_book(id)
    return book

@bookRoute.post("/new")
async def create_book(
        body:Book,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    book = await BookController.create_book(body)
    return book

@bookRoute.put("/{id}", response_model=Book)
async def update_book(
        body:BookUpdate,
        id: PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> Book:
    AuthController.check_role(decoded_token, ["admin"])
    print("Xin chao")
    book = await BookController.update_book(body, id)
    return book

@bookRoute.delete("/{id}", response_model=dict)
async def delete_book(
        id: PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    doc = await BookController.get_book(id)
    if not doc:
        raise HTTPException(status_code=404)
    is_delete = await BookController.delete_book(id)
    return is_delete
