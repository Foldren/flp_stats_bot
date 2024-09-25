from asyncio import sleep
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Page, Browser
from components.enums import BankStatus, BankType
from components.pydantic_models import MaybankData
from tasks.src.config import SECRET_KEY, PW_OPTS
from models import Bank
from modules.ocr.ocr import CaptchaSolver


class Maybank:
    def __init__(self):
        self.__root_url: str = "https://m2e.maybank.co.id"
        self.__cs: CaptchaSolver = CaptchaSolver(model_name="maybank")
        self.pages: list[Page] = []

    async def __auth(self, banks: list[Bank], browser: Browser):
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

        # Разгадываем капчу ----------------------------------------------------------------------------------------
        for page in self.pages:
            frame = page.frame_locator("#fancybox-frame")

            bytes_screen = await frame.locator('#captchaImage').screenshot()
            io = BytesIO(initial_bytes=bytes_screen)

            # Обрезаем изображение
            image = Image.open(io).crop((60, 2, 210, 32))
            captcha_code = await self.__cs.get_from_2captcha(image)
            await frame.locator('#captchaCode').type(captcha_code)

            await page.wait_for_timeout(7000)
            await frame.get_by_text(" Submit ").click()

    async def __get_pas(self) -> list[list[dict[str, str]]]:
        # Переходим во вкладку с данными аккаунта ------------------------------------------------------------------
        for page in self.pages:
            await page.get_by_text('Portfolio').click()
            await page.get_by_text('Account Management').click()
            await page.get_by_text('Overview').click()

        # Переходим во вкладку с расчетными счетами ----------------------------------------------------------------
        for page in self.pages:
            frame = page.frame_locator("#frameSet_1_8_content")
            await frame.get_by_text('DEPOSITS').click()

        # Берем из таблицы валюты и номера счета -------------------------------------------------------------------
        pages_pas = []
        for page in self.pages:
            await page.wait_for_load_state("networkidle")
            frame = page.frame_locator("#frameSet_1_8_content")
            table = frame.locator(".infotable").first.locator("tbody")
            row_count = await table.locator("tr").count()

            payment_accounts = []
            for i in range(1, row_count):
                payment_accounts.append({
                    "number": await table.locator('tr').nth(i).locator('td').nth(0).locator("#ui_button_label_").inner_text(),
                    "currency": await table.locator('tr').nth(i).locator('td').nth(1).inner_text()
                })

            pages_pas.append(payment_accounts)
            await table.locator('tr').nth(1).locator('td').nth(0).locator("a").click()

        return pages_pas

    async def __get_transactions(self, pages_pas: list[list[dict[str, str]]]):
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
                    try:
                        self.pages.pop(i)
                    except IndexError:
                        break
            i += 1

            for payment_account in pages_index_pas:
                for page in self.pages:
                    frame = page.frame_locator("#frameSet_1_8_content")
                    # todo получить последнюю дату отгрузки
                    await frame.locator("#searchCriteriaLabel2 .input_value[name='transactionHistoryVO.dateFrom']").evaluate(
                        "(element, value) => element.value = value", "2024-01-01")
                    await frame.locator("#searchCriteriaLabel1 input[name='corpVO.accountNumber']").evaluate(
                        "(element, value) => element.value = value", payment_account["number"])
                    await frame.locator("#searchCriteriaLabel1 input[name='corpVO.currencyCode']").evaluate(
                        "(element, value) => element.value = value", payment_account["currency"])
                    await frame.locator("#searchCriteriaLabel2 #ui_button_label_goButton").click()

                for page in self.pages:
                    await page.wait_for_timeout(2000)
                    frame = page.frame_locator("#frameSet_1_8_content")
                    have_next_button = True

                    while have_next_button:
                        table = frame.locator(".infotable tbody").nth(1)

                        row_count = await table.locator("tr").count()

                        if row_count > 1:
                            for i in range(1, row_count):
                                columns = table.locator('tr').nth(i).locator('td')
                                debit = await columns.nth(6).locator("div").nth(1).inner_text()
                                credit = await columns.nth(7).locator("div").nth(1).inner_text()

                                print({
                                        "date": await columns.nth(2).locator("div").nth(1).inner_text(),
                                        "description": await columns.nth(4).locator("div").nth(1).inner_text(),
                                        "id": await columns.nth(5).locator("div").nth(1).inner_text(),
                                        "amount": debit if debit != "-" else credit
                                })

                                try:
                                    pas_statements[payment_account["number"]][payment_account["currency"]].append({
                                        "date": await columns.nth(2).locator("div").nth(1).inner_text(),
                                        "description": await columns.nth(4).locator("div").nth(1).inner_text(),
                                        "id": await columns.nth(5).locator("div").nth(1).inner_text(),
                                        "amount": debit if debit != "-" else credit
                                })
                                except KeyError:
                                    pas_statements[payment_account["number"]][payment_account["currency"]] = [{
                                        "date": await columns.nth(2).locator("div").nth(1).inner_text(),
                                        "description": await columns.nth(4).locator("div").nth(1).inner_text(),
                                        "id": await columns.nth(5).locator("div").nth(1).inner_text(),
                                        "amount": debit if debit != "-" else credit
                                }]

                        print(pas_statements)

                        have_next_button = await frame.locator("#pageObject_pageIndex_nextBtn").count()

                        if have_next_button:
                            await frame.locator("#pageObject_pageIndex_nextBtn").click()


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

        async with (async_playwright() as pw):
            browser = await pw.chromium.launch(args=PW_OPTS, headless=False)
            banks = await Bank.filter(status=BankStatus.READY, type=BankType.MAYBANK)

            # Проводим авторизацию
            await self.__auth(banks, browser)

            # Получаем список расчетных счетов
            pas = await self.__get_pas()

            # Получаем список транзакций
            await self.__get_transactions(pages_pas=pas)

            await sleep(1000000)
