from os import getenv, getcwd
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = getcwd()

APP_NAME = "stats_tasks"

API_KEY_2CAPTCHA = getenv("API_KEY_2CAPTCHA")

SECRET_KEY = getenv("SECRET_KEY")

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

PW_OPTS = (
    '--start-maximized',
    '--disable-blink-features=AutomationControlled',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-infobars',
    '--disable-sync',
    '--disable-extensions',
    '--disable-extensions-file-access-check',
    '--ignore-certificate-errors',
    '--disable-default-apps',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    '--window-size=516,950',
)
