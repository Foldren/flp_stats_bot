from aiogram.fsm.state import StatesGroup, State


class MenuStates(StatesGroup):
    main = State()


class GetBanksStates(StatesGroup):
    render = State()


class CreateBankStates(StatesGroup):
    select_type = State()
    set_name = State()
    set_creds = State()


class DeleteBanksStates(StatesGroup):
    select_banks = State()


class UploadStates(StatesGroup):
    select_bank = State()
    select_interval = State()
