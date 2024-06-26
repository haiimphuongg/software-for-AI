import os
from typing import Type, TypeVar

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from pydantic import BaseModel
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from pymongo import MongoClient

from Controller.bookController import BookController
from Model.bookModel import Book

U = TypeVar('U', bound=BaseModel)
T = TypeVar('T', bound=BaseModel)
def convert_model(source_model: T, target_model_class: Type[U]) -> U:
    valid_fields = target_model_class.__fields__
    model_update = {field: value for field, value in source_model.dict().items() if field in valid_fields}
    return_instance = target_model_class(**model_update)
    return return_instance


embed_model = None

async def init_embed_model():
    global embed_model
    model_name = "BAAI/bge-base-en-v1.5"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}

    embed_model = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

def get_model():
    if embed_model is None:
        raise ValueError("Model not loaded")
    return embed_model


def get_text(book: Book):
    book_dict = book.dict()
    pop_keys = ["id", "slug", "imageUrl", "libraryID", "embeddings", "numOfRating", "totalNum"]
    old_keys = ["numPages", "publishDate", "totalBorrow", "currentNum", "avgRating", "libraryName"]
    new_keys = ["number of pages", "publish date", "total number of borrowings", "current number of book",
                "average rating", "library name"]
    for key in pop_keys:
        book_dict.pop(key, None)
    for i in range(len(old_keys)):
        book_dict[new_keys[i]] = book_dict.pop(old_keys[i])

    return str(book_dict)


vector_store = None
#
# async def init_vector_store():
#     global vector_store
#
#     print("Start get all books")
#     books_info = await BookController.get_books(get_all=True)
#     print("End get all books")
#
#     print("Connect to database")
#     client = MongoClient(os.environ.get("DB_URL"))
#     collection = client["BooksManagement"]["BookEmbedding"]
#     collection.delete_many({})
#
#     print("Create documents")
#     documents = []
#     for i in range(len(books_info)):
#         text = get_text(book=books_info[i])
#         documents.append(Document(page_content=text, metadata={"bookID" : books_info[i].id}))
#     print("End create document")
#
#     print("Start create vector store")
#     vector_store = MongoDBAtlasVectorSearch.from_documents(
#         documents= documents,
#         embedding=get_model(),
#         collection=collection,
#         index_name="vector_index"
#     )
#     print("End create vector store")

async def init_vector_store():
    global vector_store

    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
    os.environ.get("DB_URL"),
    "BooksManagement" + "." + "BookEmbedding",
    get_model(),
    index_name="vector_index",
)

def get_vector_store():
    global vector_store
    if vector_store is None:
        raise ValueError("vector_store not loaded")
    return vector_store

