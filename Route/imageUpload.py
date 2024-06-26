from fastapi import APIRouter, HTTPException
#from typing import List, Optional, Any

#from Controller.reviewController import ReviewController
#from Controller.libraryController import LibraryController

#from Model.reviewModel import BookReview, BookReviewUpdate
#from Model.bookModel import Book, BookUpdate

from beanie import PydanticObjectId

from fastapi import File, UploadFile
import firebase_admin
from firebase_admin import credentials, storage
import io 


imageUpload = APIRouter(
    tags=["Upload"]
)

#Firebase SDK
cred = credentials.Certificate("bookstoreimg-firebase-adminsdk-43y9f-d8b1b335a6.json")
firebase_admin.initialize_app(cred, {
    'storageBucket' : 'bookstoreimg.appspot.com'
})

@imageUpload.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        bucket = storage.bucket()

        blob = bucket.blob(file.filename)

        blob.upload_from_file(file.file, content_type=file.content_type)

        blob.make_public()

        return {"url": blob.public_url}

    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))

