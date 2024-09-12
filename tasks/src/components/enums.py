from enum import Enum


class BankType(str, Enum):
    MAYBANK = "Maybank"


class TransactionType(str, Enum):
    PROFIT = "Доход"
    EXPENSE = "Расход"


class BankStatus(str, Enum):
    INVALID_DATA = "Неккоретные данные входа"
    READY = "Готов к подгрузке"
