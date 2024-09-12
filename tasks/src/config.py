from os import getenv
from dotenv import load_dotenv

load_dotenv()

PG_URL = getenv('PG_URL')

APP_NAME = "stats_tasks"

API_KEY_2CAPTCHA = getenv("API_KEY_2CAPTCHA")

SECRET_KEY = getenv("SECRET_KEY")

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

BANKS_URLS = {
    'Maybank': 'https://m2e.maybank.co.id/'
}
