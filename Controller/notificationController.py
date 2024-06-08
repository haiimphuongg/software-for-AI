from datetime import date
from typing import List, Literal

from beanie import PydanticObjectId
from fastapi import HTTPException

from Database.connection import Database
from Model.notificationModel import Notification, NotificationUpdate

notification_database = Database(Notification)

class NotificationController:

    @staticmethod
    async def get_notifications(
            source: PydanticObjectId = None,
            target: PydanticObjectId = None,
            subject: str = None,
            receive_role: str = None,
            page: int = 1,
            limit: int = 10,
            sort_by: str = "_id",
            status: bool = None
    ) -> List[Notification]:
        query = {}

        if source is not None:
            query.update({"source": source})
        if target is not None:
            query.update({"target": target})
        if subject is not None:
            query.update({"subject": subject})
        if receive_role is not None:
            query.update({"receive_role": receive_role})
        if status is not None:
            query.update({"status": status})
        notifications = await notification_database.get_all(query=query, page=page, limit=limit, sort_by=sort_by)
        return notifications


    @staticmethod
    async def get_notification(
            id: PydanticObjectId = None
    ) -> Notification:
        notification = await notification_database.get_one(id=id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification

    @staticmethod
    async def create_notification(
            body: Notification
    ) -> dict:
        response = await notification_database.create(body)
        return {"message": "Notification created successfully"}

    @staticmethod
    async def delete_notification(
            id: PydanticObjectId = None
    ) -> dict:
        response = await notification_database.delete(id)
        return {"message": "Notification deleted successfully"}

    @staticmethod
    async def update_notification(
            id: PydanticObjectId = None,
            body: NotificationUpdate = None,
            target: PydanticObjectId = None
    ) -> NotificationUpdate:
        notification = await notification_database.get_one(id=id)
        print(str(notification.target))
        print(str(target))
        if notification is None:
            raise HTTPException(status_code=404, detail="Notification not found")
        elif str(notification.target) != str(target):
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        else:
            response = await notification_database.update(body=body, id=id)
        return response

    @staticmethod
    def create_notification_model(
            subject: Literal["join request", "join response", "borrow request", "delete book"],
            receive_role: Literal["user", "admin", "library"],
            source: PydanticObjectId = None,
            target: PydanticObjectId = None,
            content: str = None,
            createDate: date = None,
            status: bool = 0
    ):
        notification = {}
        notification["subject"] = subject
        notification["receive_role"] = receive_role
        notification["source"] = source
        notification["target"] = target
        notification["content"] = content
        notification["createDate"] = createDate
        notification["status"] = status

        return Notification(**notification)
