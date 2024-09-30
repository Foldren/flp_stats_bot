from asyncio import sleep
from datetime import datetime
from io import BytesIO
from json import dumps
from typing import Any
from PIL import Image
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Page, Browser
from components.enums import BankStatus, BankType
from components.pydantic_models import MaybankData
from tasks.src.config import SECRET_KEY, PW_OPTS
from models import Bank, PaymentAccount, Transaction, User
from modules.ocr.ocr import CaptchaSolver


class Maybank:
    def __init__(self):
        self.__root_url: str = "https://m2e.maybank.co.id"
        self.__cs: CaptchaSolver = CaptchaSolver(model_name="maybank")
        self.pages: list[Page] = []
        self.banks: list[Bank] = []
        self.months: list[str] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    async def __auth(self, browser: Browser):
        # Создаем страницу для каждого банка ---------------------------------------------------------------------------
        for bank in self.banks:
            context = await browser.new_context()  # Создаем отдельный контекст для каждой страницы
            page = await context.new_page()
            await page.goto(self.__root_url, timeout=10000)
            self.pages.append(page)

        # Вводим данные авторизации в банках ---------------------------------------------------------------------------
        for bank, page in zip(self.banks, self.pages):
            json_encr_data = Fernet(SECRET_KEY).decrypt(bank.json_hash_data).decode("utf-8")
            u_maybank = MaybankData.model_validate_json(json_encr_data)
            frame = page.frame_locator("#frame_7_8_content")
            # Вводим данные пользователя
            await frame.locator('[name="property1"]').type(u_maybank.corporate_id)
            await frame.locator('[name="loginId"]').type(u_maybank.user_id)
            await frame.locator('[name="loginPassword"]').type(u_maybank.password)
            # Авторизуемся
            await frame.locator('#ui_button_a_login_btn').click()

        # Разгадываем капчу --------------------------------------------------------------------------------------------
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
        # Переходим во вкладку с данными аккаунта ----------------------------------------------------------------------
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
        for page, bank in zip(self.pages, self.banks):
            await page.wait_for_load_state("networkidle")
            frame = page.frame_locator("#frameSet_1_8_content")
            table = frame.locator(".infotable").first.locator("tbody")
            row_count = await table.locator("tr").count()

            payment_accounts = []
            for i in range(1, row_count):
                payment_accounts.append({
                    "number": int(await table.locator('tr').nth(i).locator('td').nth(0).locator(
                        "#ui_button_label_").inner_text()),
                    "currency": await table.locator('tr').nth(i).locator('td').nth(1).inner_text(),
                    "bank_id": bank.id
                })

            pages_pas.append(payment_accounts)
            await table.locator('tr').nth(1).locator('td').nth(0).locator("a").click()

        return pages_pas

    async def __get_transactions(self, pages_pas: list[list[dict[str, str]]]) -> list[dict[str, Any]]:
        # Переходим на страницу с транзакциями ---------------------------------------------------------------------
        for page in self.pages:
            frame = page.frame_locator("#frameSet_1_8_content")
            await frame.get_by_text("Transaction Activity").click()
            await page.wait_for_timeout(3000)

        # Сохраняем выписки ----------------------------------------------------------------------------------------
        pas_statements = []
        i = 0
        len_pages = len(self.pages)
        while len_pages != 0:
            # Формируем вырезку расчетных счетов по индексу для каждой страницы пока они не кончатся
            pages_index_pas = []
            for pas in pages_pas:
                try:
                    pages_index_pas.append(pas[i])
                except IndexError:
                    len_pages -= 1
                    if len(self.pages) > 1:
                        self.pages.pop(i)
                    else:
                        break

            if len_pages == 0:
                break

            i += 1

            for payment_account in pages_index_pas:
                for page in self.pages:
                    frame = page.frame_locator("#frameSet_1_8_content")
                    # todo получить последнюю дату отгрузки
                    await frame.locator(
                        "#searchCriteriaLabel2 .input_value[name='transactionHistoryVO.dateFrom']").evaluate(
                        "(element, value) => element.value = value", "2024-01-01")
                    await frame.locator("#searchCriteriaLabel1 input[name='corpVO.accountNumber']").evaluate(
                        "(element, value) => element.value = value", payment_account["number"])
                    await frame.locator("#searchCriteriaLabel1 input[name='corpVO.currencyCode']").evaluate(
                        "(element, value) => element.value = value", payment_account["currency"])
                    await frame.locator("#searchCriteriaLabel2 #ui_button_label_goButton").click()
                    await page.wait_for_timeout(3000)

                for page, bank in zip(self.pages, self.banks):
                    frame = page.frame_locator("#frameSet_1_8_content")
                    have_next_button = True

                    while have_next_button:
                        await page.wait_for_timeout(3000)
                        table = frame.locator(".infotable tbody").nth(1)
                        row_count = await table.locator("tr").count()

                        if row_count > 1:
                            #todo поправить баг с первой итерацией, которая не подгружается
                            for k in range(1, row_count):
                                columns = table.locator('tr').nth(k).locator('td')
                                debit = await columns.nth(6).locator("div").nth(1).inner_text()
                                credit = await columns.nth(7).locator("div").nth(1).inner_text()

                                have_date = await columns.nth(2).locator("div").nth(1).count()
                                have_descr = await columns.nth(4).locator("div").nth(1).count()
                                have_id = await columns.nth(5).locator("div").nth(1).count()

                                if have_date:
                                    date = await columns.nth(2).locator("div").nth(1).inner_text()
                                else:
                                    date = None
                                if have_descr:
                                    descr = await columns.nth(4).locator("div").nth(1).inner_text()
                                else:
                                    descr = None
                                if have_id:
                                    trxn_id = await columns.nth(5).locator("div").nth(1).inner_text()
                                else:
                                    trxn_id = None

                                transaction = {
                                    "pa_number": payment_account["number"],
                                    "pa_currency": payment_account["currency"],
                                    "pa_bank_id": bank.id,
                                    "date": date,
                                    "description": descr,
                                    "id": trxn_id,
                                    "amount": debit if debit != "-" else "-" + credit
                                }

                                pas_statements.append(transaction)

                        have_next_button = await frame.locator("#pageObject_pageIndex_nextBtn").count()

                        if have_next_button:
                            await frame.locator("#pageObject_pageIndex_nextBtn").click()

        return pas_statements

    async def load_stats(self) -> None:
        # f = Fernet(SECRET_KEY)
        # auth_data = f.encrypt(dumps({"corporate_id": "IDUNIV16143", "user_id": "DMITR001", "password": "MayBank12345"}).encode())
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
            self.banks = await Bank.filter(status=BankStatus.READY, type=BankType.MAYBANK)

            # Проводим авторизацию
            await self.__auth(browser)

            # Получаем список расчетных счетов
            banks_pas = await self.__get_pas()

            # Получаем список транзакций
            load_transactions = await self.__get_transactions(pages_pas=banks_pas)

            # Создаем расчетные счета если их нет
            system_pas = await PaymentAccount.filter(bank__type=BankType.MAYBANK).all()

            # Формируем список системных расчетных счетов в нужном формате
            system_dict_pas = []
            for pas in system_pas:
                system_dict_pas.append({
                    "number": pas.number,
                    "currency": pas.currency,
                    "bank_id": pas.bank_id
                })

            # Формируем список всех расчетных счетов из списков
            banks_all_pas = []
            for pas in banks_pas:
                for pa in pas:
                    banks_all_pas.append(pa)

            # Формируем список расчетных счетов на создание
            pas_to_create = []
            for pa in banks_all_pas:
                if pa not in system_dict_pas:
                    pas_to_create.append(PaymentAccount(number=pa["number"],
                                                        currency=pa["currency"],
                                                        bank_id=pa["bank_id"]))

            # Создаем недостающие расчетные счета
            await PaymentAccount.bulk_create(pas_to_create, ignore_conflicts=True)

            # Формируем список транзакций на создание
            all_pas = await PaymentAccount.filter(bank__type=BankType.MAYBANK).values("id", "number", "currency",
                                                                                      "bank_id")

            print(load_transactions)
            transactions_to_create = []
            for trxn in load_transactions:
                for pa in all_pas:
                    if (pa["number"] == trxn["pa_number"] and pa["currency"] == trxn["pa_currency"] and
                            pa["bank_id"] == trxn["pa_bank_id"]):
                        split_unfrmt_date = trxn["date"].split(" ")
                        time_trxn = datetime(year=int(split_unfrmt_date[2]),
                                             month=self.months.index(split_unfrmt_date[1]) + 1,
                                             day=int(split_unfrmt_date[0]))

                        transactions_to_create.append(Transaction(
                            p_account_id=pa["id"],
                            trxn_id=trxn["id"] if trxn["id"] != "-" else None,
                            time=time_trxn,
                            amount=float(trxn["amount"].replace(",", "")),
                        ))
                        break

            await Transaction.bulk_create(transactions_to_create, ignore_conflicts=True)
            print("done")
            await sleep(1000000)
