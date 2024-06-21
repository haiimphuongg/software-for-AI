from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Any

from Controller.reviewController import ReviewController
from Controller.libraryController import LibraryController

from Model.reviewModel import BookReview, BookReviewUpdate
from Model.bookModel import Book, BookUpdate

from beanie import PydanticObjectId
from collections import Counter
import re

reviewRoute = APIRouter(
    tags=["Review"]
)

#1 Create
@reviewRoute.post("/{id}", summary="Create a new review")
async def create_review(body: BookReview) -> dict:
    try:
        newReview = await ReviewController.create(body)
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#2 Update
@reviewRoute.put("/{id}", summary="Update review information")
async def update_review(id: PydanticObjectId, content=str, rating=int) -> BookReview:
    review = await ReviewController.get_by_id(id)
    if review is not None:
        review.content = content
        review.rating = rating
    
        update = await ReviewController.update(id=id, body=update)
        if update is None:
            raise HTTPException(status_code=500, detail="Can't Update Review")
        return update
    else:
        raise HTTPException(status_code=404, detail="Can't Find Review")
    

#3 Delete
@reviewRoute.delete("/{id}", summary="Delete a review")
async def delete_review(id=PydanticObjectId) -> dict:
    response = await ReviewController.delete(id)
    return response


#4 Get 1 review by review ID
@reviewRoute.get("/info", summary="Get information of a review")
async def get_review(id:PydanticObjectId) -> BookReview:
    review = await ReviewController.get_by_id(id)
    return review

#5 Get all review of a Book
@reviewRoute.get("/BookReview", summary="Get all review of a book")
async def get_book_review(bookID: PydanticObjectId) -> List[BookReview]:
    try:
        list_review = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=bookID, userID=None,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
        return list_review
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#6 Get all review of a Library
@reviewRoute.get("/LibraryReview", summary="Get all review of all Book in a Library")
async def get_lib_review(libraryID: PydanticObjectId) -> Any:
    try:
        list_book = await ReviewController.get_book_in_lib(limit=10, page=1, sort_by="title",
                                               slug= "", genres=None, publisher=None,
                                               language=None, author=None, series=None, libraryID = libraryID,
                                               get_all=True)
        book_id_list = []
        for book in list_book:
            del book.title
            del book.slug
            del book.author
            del book.genres
            del book.description
            del book.language
            del book.numPages
            del book.imageUrl
            del book.publisher
            del book.publishDate
            del book.series
            del book.totalBorrow
            del book.totalNum
            del book.currentNum
            del book.numOfRating
            del book.avgRating
            del book.libraryID
            del book.libraryName
            id_string = str(book)
            pattern = r"id=ObjectId\('(\w+)'\)"
            match = re.search(pattern, id_string)
            book_id_list.append(match.group(1))

        lib_review = []
        for bookID in book_id_list:
            id_string = PydanticObjectId(bookID)
            list_review = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=id_string, userID=None,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
            lib_review.append(list_review)
        return lib_review
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#7 Get all User review
@reviewRoute.get("/UserReview", summary="Get all review of a User")
async def get_user_review(userID: PydanticObjectId) -> List[BookReview]:
    try:
        list_review = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=None, userID=userID,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
        return list_review
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#8 Get all Review
@reviewRoute.get("", summary="Query All Reviews")
async def get_all_review(
    limit: Optional[int] = 10,
    page: Optional[int] = 1,
    sort_by: Optional[str] = "rating",
    rating: Optional[int] = Query(None, ge=1, le=5),
    bookID: Optional[PydanticObjectId] = None,
    userID: Optional[PydanticObjectId] = None,
    startReviewDate: Optional[str] = None,
    endReviewDate: Optional[str] = None,
    get_all: Optional[bool] = False,
) -> Any:

    try:
        list_review = await ReviewController.get_all(limit=limit, page=page, sort_by=sort_by,
                                                 rating=rating, bookID=bookID, userID=userID,
                                                 startReviewDate= startReviewDate, endReviewDate=endReviewDate,
                                                 get_all=get_all)
        return list_review
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#9 Get Book Analysis
@reviewRoute.get("/BookAnalysis", summary="Get rating analysis of a book")
async def get_book_rating(bookID: PydanticObjectId) -> Any:
    try:
        list_review = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=bookID, userID=None,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)



        ratings = [review.rating for review in list_review]
        ratings_count = Counter(ratings)
        total_ratings = len(ratings)
        analysis = {
            rating: {"count": count, "percent": (count / total_ratings) * 100}
            for rating, count in ratings_count.items()
        }           
        return analysis
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#10 Get Library Analysis
@reviewRoute.get("/LibraryAnalysis", summary="Get rating analysis of a library")
async def get_lib_rating(libraryID: PydanticObjectId) -> Any:
    try:
        list_book = await ReviewController.get_book_in_lib(limit=10, page=1, sort_by="title",
                                               slug= "", genres=None, publisher=None,
                                               language=None, author=None, series=None, libraryID = libraryID,
                                               get_all=True)
        book_id_list = []
        for book in list_book:
            del book.title
            del book.slug
            del book.author
            del book.genres
            del book.description
            del book.language
            del book.numPages
            del book.imageUrl
            del book.publisher
            del book.publishDate
            del book.series
            del book.totalBorrow
            del book.totalNum
            del book.currentNum
            del book.numOfRating
            del book.avgRating
            del book.libraryID
            del book.libraryName
            id_string = str(book)
            pattern = r"id=ObjectId\('(\w+)'\)"
            match = re.search(pattern, id_string)
            book_id_list.append(match.group(1))

        ratings = []
        for bookID in book_id_list:
            id_string = PydanticObjectId(bookID)
            list_review = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=id_string, userID=None,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
            if len(list_review) > 1:
                rating = [review.rating for review in list_review]
                ratings.append(rating)
        rating_count = Counter(ratings)
        total_ratings = len(ratings)
        analysis = {
            rating: {"count": count, "percent": (count / total_ratings) * 100}
            for rating, count in ratings_count.items()
        }
        return analysis
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        #for book_review in lib_review:
        #    if book_review is not None:
        #        ratings = [review.rating for review in book_review]
        #        book_ratings.append(ratings)
        #ratings_count = Counter(book_ratings)
        #total_ratings = len(book_ratings)
        #analysis = {
        #    rating: {"count": count, "percent": (count / total_ratings) * 100}
        #    for rating, count in ratings_count.items()
        #}
