import time

from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from Controller.authController import AuthController, LoginController
from Controller.userController import UserController
from Model.userModel import User, UserUpdate
loginRoute = APIRouter()

@loginRoute.post("/login", response_model= dict)
async def login(username: str, password:str) -> dict:
    token = await LoginController.login(username, password)
    return {"access_token": token}

@loginRoute.post("/register")
async def register(body: User) -> dict:
    try:
        new_user = await UserController.register(body)
        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


