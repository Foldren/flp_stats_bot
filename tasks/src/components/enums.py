from enum import Enum


class BankType(str, Enum):
    MAYBANK = "Maybank"


class TransactionType(str, Enum):
    PROFIT = "Доход"
    EXPENSE = "Расход"


class BankStatus(str, Enum):
    INVALID_DATA = "Невалидный"
    READY = "Готов"
