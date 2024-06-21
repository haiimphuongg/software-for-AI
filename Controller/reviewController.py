from fastapi import HTTPException, Query
from typing import Any, List, Optional

from Database.connection import Database
from beanie import PydanticObjectId
from Model.reviewModel import BookReview, BookReviewUpdate
from Model.bookModel import Book
from Controller.bookController import BookController


book_database = Database(Book)
reviewDatabase= Database(BookReview)

class ReviewController:
    #1 Create
    @staticmethod
    async def create(review: BookReview) -> dict:
        await reviewDatabase.create(review)
        return {"message": "Review create successfully"}

    
    #2 Update
    async def update(body: BookReviewUpdate, id: PydanticObjectId) -> BookReview:
        review = await reviewDatabase.update(body=body, id=id)
        if not review:
            raise HTTPException(status_code=404, detail="Can't find review")
        return review

    
    #3 Delete
    async def delete(id: PydanticObjectId) -> dict:
        is_delete = await reviewDatabase.delete(id)
        if not is_delete:
            raise HTTPException(status_code=404, detail="Can't find review")
        return {"message": "Review is deleted successfully"}
    

    #4 Get 1 By ID
    async def get_by_id(id: PydanticObjectId) -> BookReview:
        review = await reviewDatabase.get_one(id)
        if not review:
            raise HTTPException(status_code=404, detail="Can't find review")
        return review

    
    #5 Get All
    async def get_all(
        limit: Optional[int] = 10,
        page: Optional[int] = 1,
        sort_by: Optional[str] = "rating",
        bookID: Optional[PydanticObjectId] = None,
        userID: Optional[PydanticObjectId] = None,
        rating: Optional[int] = Query(None, ge=1, le=5),
        startReviewDate: Optional[str] = None,
        endReviewDate: Optional[str] = None,
        get_all: Optional[bool] = False,
    ) -> List[BookReview]:
        query = {}

        if bookID is not None:
            query.update({"bookID": bookID})
        if userID is not None:
            query.update({"userID": userID})
        if rating is not None:
            query.update({"rating": rating})
        if startReviewDate is not None and endReviewDate is not None:
            query.update({"reviewDate": {"$gte": startReviewDate, "$lte": endReviewDate}})

        list_review = await reviewDatabase.get_all(limit=limit, page=page, sort_by=sort_by, query=query, get_all=get_all)

        if list_review is None:
            raise HTTPException(status_code=500, detail="Something wrong")
        
        return list_review


    #6 Get Lib Book
    async def get_book_in_lib(
        limit: Optional[int] = 10,
        page: Optional[int] = 1,
        sort_by: Optional[str] = "_id",
        slug: Optional[str] = "",
        genres: Optional[List[str]] = Query(None, alias="genres"),
        publisher: Optional[str] = Query(None, alias="publisher"),
        language: Optional[str] = Query(None, alias="language"),
        author: Optional[List[str]] = Query(None, alias="author"),
        series: Optional[List[str]] = Query(None, alias="series"),
        libraryID: Optional[PydanticObjectId] = None,
        get_all: Optional[bool] = True
    ) -> List[Book]:
        list_book = await BookController.get_books(limit=limit, page=page, sort_by=sort_by,
                                               slug= slug, genres=genres, publisher=publisher,
                                               language=language, author=author, series=series, libraryID = libraryID,
                                               get_all=get_all)
        return list_book