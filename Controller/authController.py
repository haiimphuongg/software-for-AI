import hashlib
import smtplib
from email.mime.text import MIMEText

from pydantic import EmailStr

from Database.connection import Database
from Model.userModel import User

import time

from typing import List, Optional

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.requests import Request

SECRET_KEY = "phuongdzai123"
ALGORITHM = "HS256"
userDatabase = Database(User)


class LoginController:
    @staticmethod
    async def get_token(id: str, role: str):
        expired_time = time.time() + 60 * 60 * 24
        payload = {
            'exp': expired_time,
            'id': id,
            'role': role
        }
        token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    async def login(username: str, password: str):
        query = {}
        password = hashlib.md5(password.encode()).hexdigest()
        if username is not None and password is not None:
            query.update({"username": username})
            query.update({"password": password})

        user = await userDatabase.get_all(query=query)

        if len(user) != 0:
            role = user[0].role
            user_id = str(user[0].id)
            token = await LoginController.get_token(id=user_id, role=role)
            return token, role
        else:
            raise HTTPException(status_code=401, detail="Username or password is incorrect")


    @staticmethod
    def send_email(
            from_email: EmailStr,
            app_password: EmailStr,
            to_email: EmailStr,
            body: MIMEText
    ):
        # Connect to Gmail's SMTP server using SSL.
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(from_email, password=app_password)
            # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
            smtp_server.sendmail("bobo.manager.work@gmail.com", to_email, body.as_string())
        # Print a message to console after successfully sending the email.


class AuthController(HTTPBearer):

    def __init__(self):
        super(AuthController, self).__init__(auto_error=True)

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super(AuthController, self).__call__(request)
        if credentials is not None:
            if credentials.scheme != 'Bearer':
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            elif not self.verify_token(credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            else:
                decoded_token = jwt.decode(credentials.credentials, key=SECRET_KEY, algorithms=ALGORITHM)
                return decoded_token
        else:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

    def verify_token(self, token: str):
        try:
            # algo = jwt.get_unverified_header(token)
            # if str(algo) != ALGORITHM:
            #     raise HTTPException(status_code=401, detail="Invalid authentication token")
            payload = jwt.decode(token, key=SECRET_KEY, algorithms=ALGORITHM)
        except:
            payload = None
        if payload is None:
            return False
        return True

    @staticmethod
    def check_role(decoded_token: dict = None, roles: List[str] = None) -> bool:
        if decoded_token is not None and roles is not None:
            if decoded_token['role'] in roles:
                return True
            else:
                raise HTTPException(status_code=403, detail="You do not have permission to perform this action")






