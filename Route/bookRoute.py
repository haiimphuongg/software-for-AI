import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Any

from pydantic import BaseModel

from Controller.authController import AuthController
from Controller.notificationController import NotificationController
from Model.bookModel import Book, BookUpdate
from Controller.bookController import BookController, book_database
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


@bookRoute.get("/book/filter", response_model=Any)
async def get_book_filter(
) -> Any:
    class Filter(BaseModel):
        language: str
        publisher: str
        genres: List[str]
        author: Optional[List[str]] = None
        series: Optional[List[str]] = None
    data = await book_database.model.find_all().project(Filter).to_list()

    language, publisher, genres, author, series = (set() for _ in range(5))

    for item in data:
        if item.language is not None:
            language.add(item.language)
        if item.publisher is not None:
            publisher.add(item.publisher)
        if item.genres is not None:
            genres.update(item.genres)
        if item.author is not None:
            author.update(item.author)
        if item.series is not None:
            series.update(item.series)


    return {"language": language,
            "publisher": publisher,
            "genres": genres,
            "author": author,
            "series": series}


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
        decoded_token = Depends(AuthController()),
        reason: str = "Your book violates our policies"
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    book = await BookController.get_book(id)
    library_id = book.libraryID
    book_title = book.title
    if not book:
        raise HTTPException(status_code=404)
    is_delete = await BookController.delete_book(id)

    notification = NotificationController.create_notification_model(
        status=False,
        source=decoded_token["id"],
        target=library_id,
        receive_role="library",
        content=f"The book named {book_title} has been deleted. Reason: {reason}",
        subject="delete book",
        createDate=datetime.datetime.today().date()
    )

    await NotificationController.create_notification(notification)

    return is_delete
