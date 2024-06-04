import json
import bson
from Model.bookModel import Book
from beanie import PydanticObjectId
list_id = ["665806e15e612a16a32d77f1", "665806e15e612a16a32d77f2", "665806e15e612a16a32d77f3", "665806e15e612a16a32d77f4", "665806e15e612a16a32d77f5"]
with open("C:\\Users\\PC\\Downloads\\BooksManagement.Book.json", encoding="utf8") as file:
    data = json.load(file)

for id in range(len(data)):
    data[id]["libraryID"] = { '$oid' : list_id[id % 5]}

with open(".\\data.json", "w", encoding="utf8") as file:
    json.dump(data, file)

