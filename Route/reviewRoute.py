from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Any
import pandas as pd

from Controller.userController import  UserController
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
@reviewRoute.post("/", summary="Create a new review")
async def create_review(body: BookReview) -> dict:
    try:
        newReview = await ReviewController.create(body)
        return {"message" : "Create review successfully"}
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
async def get_review(id:PydanticObjectId) -> Any:
    review_dict = []
    review = await ReviewController.get_by_id(id)
    user = await UserController.get_user(review.userID)

    del user.password
    del user.dateOfBirth
    del user.role
    del user.listOfLib
    del user.status

    review_dict.append((review, user))
    return review_dict

#5 Get all review of a Book
@reviewRoute.get("/BookReview", summary="Get all review of a book")
async def get_book_review(bookID: PydanticObjectId) -> Any:
    try:
        reviews = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=bookID, userID=None,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
        list_reviews = []
        for review in reviews:
            user = await UserController.get_user(review.userID)
            del user.password
            del user.dateOfBirth
            del user.role
            del user.listOfLib
            del user.status
            list_reviews.append((review, user))
        return list_reviews
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
            reviews = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=id_string, userID=None,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
            list_reviews = []
            for review in reviews:
                user = await UserController.get_user(review.userID)
                del user.password
                del user.dateOfBirth
                del user.role
                del user.listOfLib
                del user.status
                list_reviews.append((review, user))
            lib_review.append(list_reviews)
        return lib_review
    except HTTPException as e:
        return e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#7 Get all User review
@reviewRoute.get("/UserReview", summary="Get all review of a User")
async def get_user_review(userID: PydanticObjectId) -> Any:
    try:
        reviews = await ReviewController.get_all(limit=10, page=1, sort_by="rating",
                                                 rating=None, bookID=None, userID=userID,
                                                 startReviewDate= None, endReviewDate=None,
                                                 get_all=True)
        user = await UserController.get_user(userID)
        del user.password
        del user.dateOfBirth
        del user.role
        del user.listOfLib
        del user.status

        list_reviews = (user,reviews)

        return list_reviews
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
    get_user_info: Optional[bool] = False,
) -> Any:

    if get_user_info is False:    
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
    else:
        try:
            list_reviews_user = []
            list_review = await ReviewController.get_all(limit=limit, page=page, sort_by=sort_by,
                                                 rating=rating, bookID=bookID, userID=userID,
                                                 startReviewDate= startReviewDate, endReviewDate=endReviewDate,
                                                 get_all=get_all)

            for review in list_review:
                user = await UserController.get_user(review.userID)
                del user.password
                del user.dateOfBirth
                del user.role
                del user.listOfLib
                del user.status
                list_reviews_user.append((review, user))
            return list_reviews_user
        except HTTPException as e:
            return e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))        
