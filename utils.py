# import json
# import bson
# from Model.bookModel import Book
# from beanie import PydanticObjectId
# list_id = ["665806e15e612a16a32d77f1", "665806e15e612a16a32d77f2", "665806e15e612a16a32d77f3", "665806e15e612a16a32d77f4", "665806e15e612a16a32d77f5"]
# with open("C:\\Users\\PC\\Downloads\\BooksManagement.Book.json", encoding="utf8") as file:
#     data = json.load(file)
#
# for id in range(len(data)):
#     data[id]["libraryID"] = { '$oid' : list_id[id % 5]}
#
# with open(".\\data.json", "w", encoding="utf8") as file:
#     json.dump(data, file)
#

# import requests
# from beanie import PydanticObjectId
#
# # URL của API endpoint
# url = "http://127.0.0.1:8000/api/join-request"
#
# # Dữ liệu cần gửi (payload)
# payload = {
#     "userID": "",
#     "libraryID": "",
#     "dateCreated": "2024-06-05"
# }
#
# # Headers, nếu cần thiết
# headers = {
#     'Content-Type': 'application/json',  # Định dạng JSON
#     'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTc2OTA5NTEuNjU3ODg0NCwiaWQiOiI2MGQ5ZjRmMWUxYTNlNTZhM2MzZjNiNTciLCJyb2xlIjoiYWRtaW4ifQ.88TE9QCXZsq1JP9emL0uTm6ljRrITH2crNgwBEnJsX4'  # Nếu API yêu cầu token xác thực
# }
#
# # Thực hiện yêu cầu POST
# list_user = ["60d9f4f1e1a3e56a3c3f3b3e", "60d9f4f1e1a3e56a3c3f3b3f", "60d9f4f1e1a3e56a3c3f3b40", "60d9f4f1e1a3e56a3c3f3b41", "60d9f4f1e1a3e56a3c3f3b42"]
# list_library = ["665806e15e612a16a32d77f1", "665806e15e612a16a32d77f2", "665806e15e612a16a32d77f3", "665806e15e612a16a32d77f4", "665806e15e612a16a32d77f5"]
#
# for i in range(5):
#     for j in range(i, 5):
#         payload["userID"] = list_user[i]
#         payload["libraryID"] = list_library[j]
#         print(payload)
#         response = requests.post(url, json=payload, headers=headers)

