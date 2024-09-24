from datetime import datetime
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Page, Frame
from components.enums import BankStatus, BankType
from components.pydantic_models import MaybankData
from tasks.src.config import SECRET_KEY, PW_OPTS
from models import Bank
from modules.ocr.ocr import CaptchaSolver


class Maybank:
    def __init__(self):
        self.__root_url: str = "https://m2e.maybank.co.id"
        self.__cs: CaptchaSolver = CaptchaSolver(model_name="maybank")
        self.banks: list[Bank] = []
        self.pages: list[Page] = []
        self.us_maybank_data: list[MaybankData] = []
        self.ocr_captchas: list[str] = []

    # async def __goto_frame(self, page: Page, frame_selector: str):
    #     frame_url = await page.locator(frame_selector).get_attribute("src")
    #     full_url = self.__root_url + frame_url if self.__root_url not in frame_url else frame_url
    #
    #     await page.goto(full_url)
    #     await page.wait_for_load_state("networkidle")
    #
    # async def __set_auth_data(self, page: Page, u_maybank: MaybankData):
    #     await self.__goto_frame(page, "#frame_7_8_content")
    #
    #     # Вводим данные пользователя
    #     await page.locator('[name="property1"]').type(u_maybank.corporate_id)
    #     await page.locator('[name="loginId"]').type(u_maybank.user_id)
    #     await page.locator('[name="loginPassword"]').type(u_maybank.password)
    #
    #     # Авторизуемся
    #     await page.locator('#ui_button_a_login_btn').click()
    #
    # async def __get_captcha_screenshot(self, page: Page) -> Image:
    #     await self.__goto_frame(page, "#fancybox-frame")
    #
    #     bytes_screen = await page.locator('#captchaImage').screenshot()
    #     io = BytesIO(initial_bytes=bytes_screen)
    #
    #     # Обрезаем изображение
    #     image = Image.open(io)
    #     image = image.crop((60, 2, 210, 32))
    #
    #     return image
    #
    # @staticmethod
    # async def __send_captcha_code(page: Page, captcha: str):
    #     await page.locator('#captchaCode').type(captcha)
    #     await page.get_by_text(" Submit ").click()

    async def load_stats(self) -> None:
        # f = Fernet(SECRET_KEY)
        # auth_data = f.encrypt(dumps({"corporate_id": "IDUNIV16143", "user_id": "DMITR001", "password": "MayBank123"}).encode())
        # await User.create(id=1)
        #
        # await Bank.create(
        #     user_id=1,
        #     name="test",
        #     type="Maybank",
        #     json_hash_data=auth_data
        # )

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(args=PW_OPTS, headless=False)
            banks = await Bank.filter(status=BankStatus.READY, type=BankType.MAYBANK)

            # Создаем страницу для каждого банка -----------------------------------------------------------------------
            for bank in banks:
                context = await browser.new_context()  # Создаем отдельный контекст для каждой страницы
                page = await context.new_page()
                await page.goto(self.__root_url, timeout=10000)
                self.pages.append(page)

            # Вводим данные авторизации в банках -----------------------------------------------------------------------
            for bank, page in zip(banks, self.pages):
                json_encr_data = Fernet(SECRET_KEY).decrypt(bank.json_hash_data).decode("utf-8")
                u_maybank = MaybankData.model_validate_json(json_encr_data)
                frame = page.frame_locator("#frame_7_8_content")
                # Вводим данные пользователя
                await frame.locator('[name="property1"]').type(u_maybank.corporate_id)
                await frame.locator('[name="loginId"]').type(u_maybank.user_id)
                await frame.locator('[name="loginPassword"]').type(u_maybank.password)
                # Авторизуемся
                await frame.locator('#ui_button_a_login_btn').click()
                self.us_maybank_data.append(u_maybank)

            # Разгадываем капчу ----------------------------------------------------------------------------------------
            for page in self.pages:
                frame = page.frame_locator("#fancybox-frame")
                await page.wait_for_timeout(15000)
                await frame.get_by_text(" Submit ").click()

                # # Обрезаем изображение
                # image = await self.__get_captcha_screenshot(page)
                # # Читаем текст с помощью окр
                # # captcha_code = await self.__cs.get_from_ocr(image)
                # captcha_code = await self.__cs.get_from_2captcha(image)
                # # Вводим капчу
                # self.ocr_captchas.append(captcha_code)

            # # Разгадываем капчу через url (если надо) ------------------------------------------------------------------
            # for page, captcha_code, u_maybank in zip(self.pages, self.ocr_captchas, self.us_maybank_data):
            #     # Пробуем пройти капчу до 3 раз
            #     for i in range(3):
            #         await self.__send_captcha_code(page, captcha_code)
            #         await page.wait_for_timeout(2500)
            #         # Если не перенаправило, проходим на 2captcha
            #         if page.url == self.__root_url + "/m2e/portal/tranPortal.view?do=Captcha":
            #             # Жмем отмену
            #             await page.reload()
            #             # Снова вводим данные для входа
            #             await self.__set_auth_data(page, u_maybank)
            #             # Обрезаем изображение
            #             image = await self.__get_captcha_screenshot(page)
            #             # Проходим капчу снова, но через 2captcha
            #             captcha_code = await self.__cs.get_from_2captcha(image)
            #             await self.__send_captcha_code(page, captcha_code)

            # Переходим во вкладку с данными аккаунта ------------------------------------------------------------------
            for page in self.pages:
                await page.get_by_text('Portfolio').click()
                await page.get_by_text('Account Management').click()
                await page.get_by_text('Overview').click()

            # Переходим во вкладку с расчетными счетами ----------------------------------------------------------------
            frames = []
            for page in self.pages:
                frame = page.frame_locator("#frameSet_1_8_content")
                await frame.get_by_text('DEPOSITS').click()
                frames.append(frame)

            # Берем из таблицы валюты и номера счета -------------------------------------------------------------------
            pages_pas = []
            for frame, page in zip(frames, self.pages):
                table = frame.locator(".infotable").first.locator("tbody")
                print()
                row_count = await table.locator("tr").count()

                payment_accounts = []
                for i in range(1, row_count):
                    payment_accounts.append({
                        "number": await table.locator('tr').nth(i).locator('td').nth(0).locator("#ui_button_label_").inner_text(),
                        "currency": await table.locator('tr').nth(i).locator('td').nth(1).inner_text()
                    })

                pages_pas.append(payment_accounts)
                await table.locator('tr').nth(1).locator('td').nth(0).locator("a").click()

            # Переходим на страницу с транзакциями ---------------------------------------------------------------------
            for page in self.pages:
                frame = page.frame_locator("#frameSet_1_8_content")
                await frame.get_by_text("Transaction Activity").click()

            # Сохраняем выписки ----------------------------------------------------------------------------------------
            pas_statements = {}
            i = 0
            while self.pages:
                # Формируем вырезку расчетных счетов по индексу для каждой страницы пока они не кончатся
                pages_index_pas = []
                for pas in pages_pas:
                    try:
                        pages_index_pas.append(pas[i])
                    except IndexError:
                        self.pages.pop(i)
                        if not self.pages:
                            break
                i += 1

                for payment_account in pages_index_pas:
                    for page in self.pages:
                        frame = page.frame_locator("#frameSet_1_8_content")
                        # todo получить последнюю дату отгрузки
                        await frame.locator("input[name='transactionHistoryVO.dateFrom'][type='hidden']").evaluate("(element, value) => element.value = value", "2024-01-01")
                        await frame.locator("input[name='corpVO.accountNumber']").evaluate("(element, value) => element.value = value", payment_account["number"])
                        await frame.locator("input[name='corpVO.currencyCode']").evaluate("(element, value) => element.value = value", payment_account["currency"])
                        await frame.locator("#ui_button_label_goButton").nth(1).click()

                    for page in self.pages:
                        frame = page.frame_locator("#frameSet_1_8_content")
                        have_next_button = True

                        while have_next_button:
                            table = frame.locator(".infotable").locator("tbody").nth(2)
                            row_count = await table.locator("tr").count()
                            print(await table.inner_html())
                            for i in range(1, row_count):
                                columns = table.locator('tr').nth(i).locator('td')
                                debit = (await columns.nth(6).locator("div").nth(1).inner_text())[1:-1]
                                credit = (await columns.nth(7).locator("div").nth(1).inner_text())[1:-1]

                                pas_statements[payment_account["number"]].append({
                                    "date": (await columns.nth(2).locator("div").nth(1).inner_text())[1:-1],
                                    "description": (await columns.nth(4).locator("div").nth(1).inner_text())[1:-1],
                                    "id": (await columns.nth(5).locator("div").nth(1).inner_text())[1:-1],
                                    "amount": debit if debit != "-" else credit
                                })

                            have_next_button = await frame.locator("#pageObject_pageIndex_nextBtn").count()

                            if have_next_button:
                                await frame.locator("#pageObject_pageIndex_nextBtn").click()

            print(pas_statements)

            await page.wait_for_timeout(1000000)
