from aiogram_dialog import Window, ShowMode
from aiogram_dialog.widgets.kbd import Group, Start
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.text import Multi, Const, Format
from components.states import MenuStates, GetBanksStates


w_main = Window(
    Multi(
        Format("👋 Вы в главном меню, <b>{event.from_user.username}</b>"),
        Const(f"<u>Рабочие кнопки бота по чтению выписок ⚙️</u>\n"
              f"<b>🔹 Банки</b> - добавить банки для подгрузки выписок\n"
              f"<b>🔹 Выгрузка АО</b> - выгрузить выписки в формате Excel файла, за определенный интервал."),
        sep="\n\n"
    ),
    # Group(
        Start(text=Const("Банки"), id="banks", state=GetBanksStates.render, show_mode=ShowMode.DELETE_AND_SEND),
        # Start(
        #     text=Const("Выгрузка"),
        #     id="upload",
        #     state=UploadStates.select_bank,
        # ),
        # width=2
    # ),
    state=MenuStates.main,
    markup_factory=ReplyKeyboardFactory(resize_keyboard=True, input_field_placeholder=Const("Главное меню"))
)
