from datetime import datetime, timedelta
from io import BytesIO
from typing import Any
from PIL import Image
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Page, Browser
from models import BankStatus, BankType
from components.pydantic_models import MaybankData
from modules.logger import Logger
from config import SECRET_KEY, PW_OPTS, APP_NAME, TORTOISE_CONFIG, BOT
from models import Bank, PaymentAccount, Transaction
from modules.ocr.ocr import CaptchaSolver


class Maybank:
    def __init__(self):
        self.__root_url: str = "https://m2e.maybank.co.id"
        self.__cs: CaptchaSolver = CaptchaSolver()
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
        for i, page in enumerate(self.pages):
            try:
                frame = page.frame_locator("#fancybox-frame")

                while True:
                    bytes_screen = await frame.locator('#captchaImage').screenshot()
                    io = BytesIO(initial_bytes=bytes_screen)

                    # Обрезаем изображение
                    image = Image.open(io).crop((60, 2, 210, 32))

                    # Получаем капчу
                    captcha_code = await self.__cs.get_from_anticaptcha(image)

                    if captcha_code.islower() or captcha_code.isupper() or (not captcha_code.isalnum()) or (len(captcha_code) != 6):
                        await frame.locator('#refreshCaptchaImg').click()
                        await page.wait_for_timeout(1500)
                    else:
                        await frame.locator('#captchaCode').type(captcha_code)
                        break

                await frame.get_by_text(" Submit ").click()

            except Exception:
                self.pages.pop(i)
                self.banks.pop(i)

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
            await page.wait_for_timeout(4000)

        # Сохраняем выписки ----------------------------------------------------------------------------------------
        current_pas = await PaymentAccount.filter(bank__type=BankType.MAYBANK).all()
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
                for page, bank in zip(self.pages, self.banks):
                    start_date = (datetime(year=datetime.now().year, month=1, day=1)).strftime("%Y-%m-%d")
                    for pa in current_pas:
                        if (pa.bank_id == bank.id) and (pa.number == payment_account["number"]) and (
                                pa.currency == payment_account["currency"]):
                            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                            break

                    frame = page.frame_locator("#frameSet_1_8_content")
                    # todo получить последнюю дату отгрузки
                    await frame.locator(
                        "#searchCriteriaLabel2 .input_value[name='transactionHistoryVO.dateFrom']").evaluate(
                        "(element, value) => element.value = value", start_date)
                    await frame.locator("#searchCriteriaLabel1 input[name='corpVO.accountNumber']").evaluate(
                        "(element, value) => element.value = value", payment_account["number"])
                    await frame.locator("#searchCriteriaLabel1 input[name='corpVO.currencyCode']").evaluate(
                        "(element, value) => element.value = value", payment_account["currency"])
                    await frame.locator("#searchCriteriaLabel2 #ui_button_label_goButton").click()
                    await page.wait_for_timeout(4000)

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
        await Logger(APP_NAME).info(msg="Начинаю подгрузку выписок из Maybank.", func_name="maybank.load_stats")

        async with (async_playwright() as pw):
            browser = await pw.chromium.launch(args=PW_OPTS, headless=True, chromium_sandbox=False, devtools=False)
            self.banks = await Bank.filter(status=BankStatus.READY, type=BankType.MAYBANK)

            # Проводим авторизацию
            await self.__auth(browser)

            # Получаем список расчетных счетов
            banks_pas = await self.__get_pas()

            # Получаем список транзакций
            load_transactions = await self.__get_transactions(pages_pas=banks_pas)

            if load_transactions:
                for bank in self.banks:
                    new_trxns_msg = f"<b>🟢 Новые выписки по {bank.type} банку: {bank.name}</b>\n\n"
                    pa_name = ""
                    for transaction in load_transactions:
                        if pa_name != str(transaction["pa_number"]) + " " + transaction["pa_currency"]:
                            pa_name = str(transaction["pa_number"]) + " " + transaction["pa_currency"]
                            new_trxns_msg += f"<b>📑 Счёт {pa_name}</b>\n\n"

                        if transaction["pa_bank_id"] == bank.id:
                            new_trxns_msg += f"<u>ID:</u> {transaction['id']}\n"
                            new_trxns_msg += f"<u>Дата:</u> {transaction['date']}\n"
                            new_trxns_msg += f"<u>Описание:</u> {transaction['description']}\n"
                            new_trxns_msg += f"<u>Сумма:</u> {transaction['amount']}\n\n"

                    await BOT.send_message(chat_id=bank.user_id, text=new_trxns_msg)

                # Формируем список расчетных счетов на создание
                pas_to_create = []
                for pas in banks_pas:
                    for pa in pas:
                        pas_to_create.append(
                            PaymentAccount(number=pa["number"], currency=pa["currency"], bank_id=pa["bank_id"]))

                # Создаем недостающие расчетные счета
                await PaymentAccount.bulk_create(pas_to_create, ignore_conflicts=True)

                # Формируем список транзакций на создание --------------------------------------------------------------
                all_pas = await PaymentAccount.filter(bank__type=BankType.MAYBANK).values("id", "number", "currency",
                                                                                          "bank_id")
                transactions_to_create = []
                for trxn in load_transactions:
                    for pa in all_pas:
                        if (pa["number"] == trxn["pa_number"]) and (pa["currency"] == trxn["pa_currency"]) and (
                                pa["bank_id"] == trxn["pa_bank_id"]):
                            split_unfrmt_date = trxn["date"].split(" ")
                            time_trxn = datetime(year=int(split_unfrmt_date[2]),
                                                 month=self.months.index(split_unfrmt_date[1]) + 1,
                                                 day=int(split_unfrmt_date[0]))

                            transactions_to_create.append(Transaction(
                                p_account_id=pa["id"],
                                trxn_id=trxn["id"] if trxn["id"] != "-" else None,
                                time=time_trxn,
                                description=trxn["description"],
                                amount=float(trxn["amount"].replace(",", "")),
                            ))
                            break

                await Transaction.bulk_create(transactions_to_create, ignore_conflicts=True)

                await Logger(APP_NAME).success(msg="Подгрузка завершена.", func_name="maybank.load_stats")
            else:
                await Logger(APP_NAME).info(msg="Нет новых выписок.", func_name="maybank.load_stats")


# async def test():
#     await Tortoise.init(TORTOISE_CONFIG)
#     await Tortoise.generate_schemas(safe=True)
#     await Maybank().load_stats()
#
#
# if __name__ == '__main__':
#     run(test())
