from asyncio import run
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tortoise import run_async, Tortoise
from config import PG_URL
from init import start_sheduler

# Инициализируем шедулер
scheduler = AsyncIOScheduler()


@scheduler.scheduled_job(trigger="cron", hour=3, minute=0)
async def load_statements():
    """
    Таск на подгрузку выписок
    """


if __name__ == '__main__':
    run_async(Tortoise.init(db_url=PG_URL, modules={'api': ['db_models.api']}))  # Подключаем бд
    run(start_sheduler(scheduler))  # Запускаем шедулер
