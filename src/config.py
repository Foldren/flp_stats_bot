from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("TOKEN")

BANKS = ("Maybank",)

BANKS_CREDS = {
    "Maybank": ("corporate_id", "user_id", "password",)
}

SQL_URL = getenv("SQL_URL")

REDIS_URL = getenv("REDIS_URL")

SECRET_KEY = getenv("SECRET_KEY")
