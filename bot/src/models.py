from enum import Enum
from tortoise import Model
from tortoise.fields import BigIntField, \
    CharEnumField, ForeignKeyRelation, ForeignKeyField, OnDelete, ReverseRelation, CharField, BinaryField, \
    DatetimeField, FloatField


# Enums ----------------------------------------------------------------------------------------------------------------
class BankType(str, Enum):
    MAYBANK = "Maybank"


class BankStatus(str, Enum):
    INVALID_DATA = "Невалидный"
    READY = "Готов"


# Models ---------------------------------------------------------------------------------------------------------------
class User(Model):
    id = BigIntField(pk=True)  # chat_id
    banks: ReverseRelation['Bank']


class Bank(Model):
    id = BigIntField(pk=True)
    user: ForeignKeyRelation['User'] = ForeignKeyField('models.User', on_delete=OnDelete.CASCADE, related_name="banks")
    p_accounts: ReverseRelation['PaymentAccount']
    name = CharField(max_length=20)
    type = CharEnumField(enum_type=BankType)
    json_hash_data = BinaryField()
    status = CharEnumField(enum_type=BankStatus, default=BankStatus.READY)


class PaymentAccount(Model):
    id = BigIntField(pk=True)
    bank: ForeignKeyRelation['PaymentAccount'] = ForeignKeyField('models.Bank', on_delete=OnDelete.CASCADE,
                                                                 related_name="payment_accounts")
    transactions: ReverseRelation['Transaction']
    number = BigIntField()
    currency = CharField(max_length=10)

    class Meta:
        unique_together = ("bank_id", "number", "currency")


class Transaction(Model):
    id = BigIntField(pk=True)
    p_account: ForeignKeyRelation['PaymentAccount'] = ForeignKeyField('models.PaymentAccount', on_delete=OnDelete.CASCADE,
                                                                      related_name="transactions")
    trxn_id = CharField(max_length=40, null=True)
    time = DatetimeField()
    amount = FloatField()