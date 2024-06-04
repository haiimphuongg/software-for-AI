from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import FastAPI, APIRouter, Depends

from Controller.authController import AuthController
from Model.borrowModel import Borrow, BorrowUpdate
from Controller.borrowController import BorrowController
borrowRoute = APIRouter(tags=['Borrow'])

@borrowRoute.get('', response_model=List[Borrow])
async def get_borrows(
        libraryID: Optional[PydanticObjectId] = None,
        userID: Optional[PydanticObjectId] = None,
        sort_by: Optional[str] = "_id",
        limit: Optional[int] = 10,
        page:  Optional[int] = 1,
        get_all: Optional[bool] = False,
        decoded_token = Depends(AuthController())
) -> List[Borrow]:
    AuthController.check_role(decoded_token, ["admin"])
    borrows = await BorrowController.get_borrows(libraryID=libraryID,
                                                 userID=userID,
                                                 sort_by=sort_by,
                                                 limit=limit,
                                                 page=page,
                                                 get_all=get_all)
    return borrows

@borrowRoute.get('/{borrowID}', response_model=Borrow)
async def get_borrow(
        borrowID: PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> Borrow:
    AuthController.check_role(decoded_token, ["admin"])
    return await BorrowController.get_borrow(borrowID=borrowID)

@borrowRoute.post('', response_model=dict)
async def create_borrow(
        body: Borrow,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    response = await BorrowController.create_borrow(body=body)
    return response

@borrowRoute.delete('/{borrowID}', response_model=dict)
async def delete_borrow(
        borrowID: PydanticObjectId,
        decoded_token = Depends(AuthController())
) -> dict:
    AuthController.check_role(decoded_token, ["admin"])
    response = await BorrowController.delete_borrow(borrowID)
    return response

@borrowRoute.put('/{borrowID}', response_model=Borrow)
async def update_borrow(
        borrowID: PydanticObjectId,
        body: BorrowUpdate,
        decoded_token = Depends(AuthController())
) -> Borrow:
    AuthController.check_role(decoded_token, ["admin"])
    borrow = await BorrowController.update_borrow(borrowID=borrowID, body=body)
    return borrow

