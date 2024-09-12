from asyncio import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import APP_NAME
from modules.logger import Logger


async def start_sheduler(sch: AsyncIOScheduler) -> None:
    """
    Функция для запуска APSheduler
    (по инструкции https://github.com/agronholm/apscheduler/blob/3.x/examples/schedulers/asyncio_.py)
    :param sch: объект таск менеджера AsyncIOScheduler
    """
    try:
        sch.start()
        await Logger(APP_NAME).success(msg="Планировщик запущен.", func_name="startup")
        while True:
            await sleep(1000)
    except (KeyboardInterrupt, SystemExit):
        pass