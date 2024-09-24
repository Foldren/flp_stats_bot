from asyncio import run
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tortoise import run_async, Tortoise
from config import TORTOISE_CONFIG
from init import start_sheduler, init_db
from modules.playwright.maybank import Maybank

# Инициализируем шедулер
scheduler = AsyncIOScheduler()


# @scheduler.scheduled_job(trigger="cron", hour=3, minute=0)
# async def load_statements():
#     """
#     Таск на подгрузку выписок
#     """


if __name__ == '__main__':
    run_async(init_db())  # Подключаем бд
    run(Maybank().load_stats())
    # run(start_sheduler(scheduler))  # Запускаем шедулер
