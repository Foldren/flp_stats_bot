import time
from asyncio import run
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Page
from components.enums import BankStatus, BankType
from components.pydantic_models import MaybankData
from ...config import SECRET_KEY, PW_OPTS, BANKS_URLS
from models import Bank
from modules.ocr import CaptchaSolver

cs = CaptchaSolver()


async def __set_auth_data(page: Page, u_maybank: MaybankData):
    frame = page.frame("frame_7_8_content")
    # Вводим данные пользователя
    await frame.locator('[name="property1"]').click()
    await page.keyboard.press(u_maybank.corporate_id)
    await frame.locator('[name="loginId"]').click()
    await page.keyboard.press(u_maybank.user_id)
    await frame.locator('[name="loginPassword"]').click()
    await page.keyboard.press(u_maybank.password)
    # Авторизуемся
    await frame.locator('#ui_button_a_login_btn').click()


async def __get_captcha_screenshot(page: Page) -> Image:
    frame = page.frame("fancybox-frame")
    bytes_screen = await frame.locator('#captchaImage').screenshot()
    io = BytesIO(initial_bytes=bytes_screen)
    # Обрезаем изображение
    image = Image.open(io)
    image = image.crop((60, 2, 210, 32))

    return image


async def __send_captcha_code(page: Page, captcha: str):
    frame = page.frame("fancybox-frame")
    await frame.locator('#captchaCode').click()
    await page.keyboard.press(captcha)
    await frame.locator("#ui_button_label_btn").click()


async def load_st() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=PW_OPTS)
        banks = await Bank.filter(status=BankStatus.READY, type=BankType.MAYBANK)

        # Создаем страницу для каждого банка ---------------------------------------------------------------------------
        pages = []
        for bank in banks:
            context = await browser.new_context()  # Создаем отдельный контекст для каждой страницы
            page = await context.new_page()
            await page.goto(BANKS_URLS["Maybank"])
            pages.append(page)

        # Вводим данные авторизации в банках ---------------------------------------------------------------------------
        us_maybank_data = []
        for bank, page in zip(banks, pages):
            frame = page.frame("frame_7_8_content")
            json_encr_data = Fernet(SECRET_KEY).encrypt(bank.json_hash_data).decode("utf-8")
            u_maybank = MaybankData.model_validate_json(json_encr_data)
            us_maybank_data.append(u_maybank)
            await __set_auth_data(page, u_maybank)

        # Разгадываем капчу через окр ----------------------------------------------------------------------------------
        current_urls = []
        images = []
        for page in pages:
            # Обрезаем изображение
            image = await __get_captcha_screenshot(page)
            images.append(image)
            # Читаем текст с помощью окр
            captcha_code = await cs.get_from_ocr(image)
            current_urls.append(page.url)
            # Вводим капчу
            await __send_captcha_code(page, captcha_code)

        # Разгадываем капчу через url (если надо) ----------------------------------------------------------------------
        for c_url, image, page, u_maybank in zip(current_urls, images, pages, us_maybank_data):
            # Пробуем пройти капчу до 2 раз
            for i in range(2):
                # Если не перенаправило, проходим на 2captcha
                if page.url == c_url:
                    # Жмем отмену
                    await frame.locator("#ui_button_label_btn").click()
                    # Снова вводим данные для входа
                    await __set_auth_data(page, u_maybank)
                    # Обрезаем изображение
                    image = await __get_captcha_screenshot(page)
                    # Проходим капчу снова, но через 2captcha
                    captcha_code = await cs.get_from_2captcha(image)
                    await __send_captcha_code(page, captcha_code)
                else:
                    break


if __name__ == '__main__':
    run(load_st())
    time.sleep(999999)
