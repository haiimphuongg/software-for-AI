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
from dotenv import load_dotenv

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

load_dotenv()

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


retriever = None


def init_retriever():
    global retriever
    retriever = get_vector_store().as_retriever(k = 3)


def get_retriever():
    global retriever
    if retriever is None:
        raise ValueError("retriever not loaded")
    return retriever


conversational_rag_chain = None
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    global store
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


async def init_conversational_rag_chain():
    global conversational_rag_chain, store
    init_retriever()
    llm = HuggingFaceEndpoint(
        repo_id = "meta-llama/Meta-Llama-3-8B-Instruct",
        task="text-generation",
        max_new_tokens=1024,
        temperature= 0.05
    )
    # Contextualize question #
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, get_retriever(), contextualize_q_prompt
    )

    # Answer question #
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If the provided context does not contain "
        "enough information to answer the question, respond with "
        "\"I do not have that information.\" Use three sentences "
        "maximum and keep the answer concise."
        "\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # Statefully manage chat history #

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

def get_conversational_rag_chain():
    global conversational_rag_chain
    if conversational_rag_chain is None:
        raise Exception("Conversational Rag chain is not initialized")
    return conversational_rag_chain


