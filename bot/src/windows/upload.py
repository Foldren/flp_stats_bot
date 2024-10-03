from datetime import date, datetime
from aiogram import F
from aiogram_dialog import Window
from aiogram_dialog.widgets.kbd import Cancel, ScrollingGroup, Select, Row, Back, CalendarConfig, Calendar
from aiogram_dialog.widgets.text import Multi, Const, Format
from components.getters import get_banks
from components.states import UploadStates
from events.stats.upload import on_select_bank, on_select_start_date, on_select_end_date


w_select_bank = Window(
    Multi(
        Const(f"<b>Выгрузка:</b> <i>(шаг 1)</i>"),
        Const(f"👉 Здесь вы можете выгрузить транзакции по банкам, для начала выберите банк:"),
        sep="\n\n",
        when=F["not_empty"]
    ),
    Multi(
        Const(f"<b>Выгрузка:</b> <i>(шаг 1)</i>"),
        Const(f"🤷‍♂️ Пока что вы не добавили ни одного банка."),
        sep="\n\n",
        when=~F["not_empty"]
    ),
    Cancel(text=Const("Отмена ⛔️️")),
    ScrollingGroup(
        Select(
            text=Format("{item.name}"),
            items="banks",
            item_id_getter=lambda bank: bank.id,
            on_click=on_select_bank,
            id="s_banks"
        ),
        id="sc_banks",
        width=2,
        height=3,
        hide_on_single_page=True,
        when=F["not_empty"]
    ),
    state=UploadStates.select_bank,
    getter=get_banks
)

w_select_start_date = Window(
    Multi(
        Const(f"<b>Выгрузка:</b> <i>(шаг 2)</i>"),
        Const(f"📆 Выберите начальную дату отгрузки:"),
        Format("<u>Выбран банк</u>: {dialog_data[bank_name]}"),
        sep="\n\n"
    ),
    Calendar(id='upload_s_calendar',
             on_click=on_select_start_date,
             config=CalendarConfig(min_date=date(year=1991, month=1, day=1), max_date=datetime.now().date())
             ),
    Row(
        Back(text=Const("Назад ⬅️")),
        Cancel(text=Const("Отмена ⛔️"))
    ),
    state=UploadStates.select_start_date,
)

w_select_end_date = Window(
    Multi(
        Const(f"<b>Выгрузка:</b> <i>(шаг 2)</i>"),
        Const(f"📆 Выберите итоговую дату отгрузки:"),
        Format("<u>Выбран банк</u>: {dialog_data[bank_name]}\n"
               "<u>Выбрана стартовая дата</u>: {dialog_data[start_date]}"),
        sep="\n\n"
    ),
    Calendar(id='upload_s_calendar',
             on_click=on_select_end_date,
             config=CalendarConfig(min_date=date(year=1991, month=1, day=1), max_date=datetime.now().date())
             ),
    Row(
        Back(text=Const("Назад ⬅️")),
        Cancel(text=Const("Отмена ⛔️"))
    ),
    state=UploadStates.select_end_date,
)
