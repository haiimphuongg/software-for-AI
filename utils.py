import json
import bson
from Model.bookModel import Book
from beanie import PydanticObjectId
list_id = ["665806e15e612a16a32d77f1", "665806e15e612a16a32d77f2", "665806e15e612a16a32d77f3", "665806e15e612a16a32d77f4", "665806e15e612a16a32d77f5"]
list_name = ["Nguyen Phuong's Library","Books of Anh Long", "VMT Central Library", "Nguyen Anh Tu Library", "Nguyen's Books Library"]
with open("D:\\importnp\\Y3-HK2\\introSE\\BoBo\\BooksManagement.Book.json", encoding="utf8") as file:
    data = json.load(file)

for id in range(len(data)):
    data[id]["libraryName"] = list_name[id % 5]
    data[id]["libraryID"] = { '$oid' : list_id[id % 5]}
with open(".\\BooksManagement.Book.json", "w", encoding="utf8") as file:
    json.dump(data, file)


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

#
# import smtplib
# from email.mime.text import MIMEText
#
# # Define the subject and body of the email.
# subject = "Email Subject"
# body = "This is the body of the text message"
# # Define the sender's email address.
# sender = "bobo.manager.work@gmail.com"
# # List of recipients to whom the email will be sent.
# recipients = ["liophuong81@gmail.com", "phuonglt81ldc@gmail.com"]
# # Password for the sender's email account.
# password = "jxwpzuvxrowxttpa"
#
#
# def send_email(subject, body, sender, recipients, password):
#     # Create a MIMEText object with the body of the email.
#     msg = MIMEText(body)
#     # Set the subject of the email.
#     msg['Subject'] = "Urgent"
#     # Set the sender's email.
#     msg['From'] = sender
#     # Join the list of recipients into a single string separated by commas.
#     msg['To'] = ', '.join(recipients)
#
#     # Connect to Gmail's SMTP server using SSL.
#     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
#         smtp_server.login('bobo.manager.work@gmail.com', password= password)
#         # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
#         smtp_server.sendmail(sender, recipients, msg.as_string())
#     # Print a message to console after successfully sending the email.
#     print("Message sent!")
#
# send_email("Test", "Please give me more information about tomorrow session!", sender, recipients, password)
