import hashlib

hashed_password = hashlib.md5("123".encode()).hexdigest()
print(hashed_password)