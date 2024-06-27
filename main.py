from fastapi import FastAPI

from Route.chatRoute import chatRoute
from Route.bookRoute import bookRoute
from Route.borrowRoute import borrowRoute
from Route.libraryRoute import libraryRoute
from Route.loginRoute import loginRoute
from Route.joinRequestRoute import joinRequestRoute
from Route.userRoute import userRoute
import uvicorn
from Database.connection import settings
from fastapi.middleware.cors import CORSMiddleware
from Utils.Utils import init_embed_model, init_vector_store, init_conversational_rag_chain

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookRoute, prefix="/api/books")
app.include_router(libraryRoute, prefix="/api/libraries")
app.include_router(borrowRoute, prefix="/api/borrows")
app.include_router(joinRequestRoute, prefix="/api/join-request")
app.include_router(userRoute, prefix="/api/user")
app.include_router(loginRoute, prefix="/api")
app.include_router(chatRoute, prefix="/api/chat")


@app.on_event("startup")
async def init_db():
    await settings.initialize_database()
    print("Initialized database")
    await init_embed_model()
    print("Initialized model")
    await init_vector_store()
    print("Initialized vector store")
    await init_conversational_rag_chain()
    print("Initialized conversational rag chain")

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
