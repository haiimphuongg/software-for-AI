import time

from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
import jwt
from Controller.authController import AuthController, LoginController

loginRoute = APIRouter()

@loginRoute.post("", response_model= dict)
async def login(username: str, password:str) -> dict:
    token = await LoginController.login(username, password)
    return {"access_token": token}



