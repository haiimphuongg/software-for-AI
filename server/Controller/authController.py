from Database.connection import Database
from Model.userModel import User

import time

from typing import List

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
        if username is not None and password is not None:
            query.update({"username": username})
            query.update({"password": password})

        user = await userDatabase.get_all(query=query)

        if len(user) != 0:
            role = user[0].role
            id = str(user[0].id)
            token = await LoginController.get_token(id=id, role=role)
            return token
        else:
            raise HTTPException(status_code=401, detail="Username or password is incorrect")


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
            raise HTTPException(status_code=401, detail="Invalid authentication code")

    def verify_token(self, token: str):
        try:
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





