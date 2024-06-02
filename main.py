from fastapi import FastAPI
from Route.bookRoute import bookRoute
from Route.borrowRoute import borrowRoute
from Route.libraryRoute import libraryRoute
from Route.loginRoute import loginRoute
from Route.joinRequestRoute import joinRequestRoute
from Route.userRoute import userRoute
import uvicorn
from Database.connection import settings

app = FastAPI()


app.include_router(bookRoute, prefix="/books")
app.include_router(libraryRoute, prefix="/libraries")
app.include_router(borrowRoute, prefix="/borrows")
app.include_router(joinRequestRoute, prefix="/join-request")
app.include_router(userRoute, prefix="/user")
app.include_router(loginRoute, prefix="")


@app.on_event("startup")
async def init_db():
    await settings.initialize_database()


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)