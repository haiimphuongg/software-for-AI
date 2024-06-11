import random
import smtplib
import string
import time
from email.mime.text import MIMEText
from typing import Optional

from fastapi import FastAPI, HTTPException, status, APIRouter, Depends, BackgroundTasks
from pydantic import EmailStr

from Controller.authController import AuthController, LoginController
from Controller.userController import UserController
from Model.userModel import User, UserUpdate
from Utils.Utils import convert_model

loginRoute = APIRouter()

@loginRoute.post("/login", response_model= dict)
async def login(username: str, password:str) -> dict:
    token, role = await LoginController.login(username, password)
    return {"access_token": token, "role": role}

@loginRoute.post("/register",
                 summary="CREATE a new user account with default role is User (can not be changed)")
async def register(body: User) -> dict:
    try:
        body.role = "user"
        body.status = 1
        print(body)
        new_user = await UserController.register(body)

        return new_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@loginRoute.put("/forget-password",
                summary="FORGET PASSWORD for all rules")
async def forget_password(
        background_tasks: BackgroundTasks,
        username: Optional[str] = None,
        email: Optional[EmailStr] = None,
):
    def generate_random_string(length=16):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    if username is None and email is None:
        raise HTTPException(status_code=500, detail="You have to provide username or email")
    user = await UserController.get_all_user(username=username, email=email)

    if len(user) == 0:
        raise HTTPException(status_code=404, detail="User not found")

    new_password = generate_random_string(16)
    user[0].password = new_password
    await UserController.update_user(body=convert_model(user[0], UserUpdate), id=user[0].id, encoded=False)

    email = user[0].email
    msg = MIMEText(f"Hello, \nWe noticed that you recently requested a password reset.\nHere is your new password:\n{new_password}")
    # Set the subject of the email.
    msg['Subject'] = "[PASSWORD RESET]"
    # Set the sender's email.
    msg['From'] = "bobo.manager.work@gmail.com"
    # Join the list of recipients into a single string separated by commas.
    msg['To'] = email

    background_tasks.add_task(LoginController.send_email,"bobo.manager.work@gmail.com", "ordqoggmfcaxdkmw", email, msg)

    return {"message": "Password changed successfully"}


