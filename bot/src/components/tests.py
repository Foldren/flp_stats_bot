from json import dumps
from cryptography.fernet import Fernet
from config import SECRET_KEY

f = Fernet(SECRET_KEY)
auth_data = f.encrypt(dumps({"corporate_id": "IDUNIV16143", "user_id": "DMITR001", "password": "MayBank12345"}).encode())
print(auth_data)