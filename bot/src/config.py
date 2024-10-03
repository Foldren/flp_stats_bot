from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("TOKEN")

BANKS = ("Maybank",)

BANKS_CREDS = {
    "Maybank": ("corporate_id", "user_id", "password",)
}

TORTOISE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "user": getenv("PG_USER"),
                "password": getenv("PG_PSW"),
                "host": getenv("PG_HOST"),
                "port": getenv("PG_PORT"),
                "database": getenv("PG_DB"),
            }
        }
    },
    "apps": {
        "models": {"models": ["models"], "default_connection": "default"},
    },
    'use_tz': True,
    'timezone': 'Europe/Moscow'
}

REDIS_URL = getenv("REDIS_URL")

SECRET_KEY = getenv("SECRET_KEY")

EXCEL_TEMPLATE_PATH = "./.excel_template.xlsx"
