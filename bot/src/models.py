from tortoise import Model
from tortoise.fields import BigIntField, \
    CharEnumField, ForeignKeyRelation, ForeignKeyField, OnDelete, ReverseRelation, CharField, BinaryField
from components import enums


class User(Model):
    id = BigIntField(pk=True)  # chat_id
    banks: ReverseRelation['Bank']


class Bank(Model):
    id = BigIntField(pk=True)
    user: ForeignKeyRelation['User'] = ForeignKeyField('bot.User', on_delete=OnDelete.CASCADE, related_name="banks")
    p_accounts: ReverseRelation['PaymentAccount']
    name = CharField(max_length=20)
    type = CharEnumField(enum_type=enums.BankType)
    json_hash_data = BinaryField()
    status = CharEnumField(enum_type=enums.BankStatus, default=enums.BankStatus.READY)


class PaymentAccount(Model):
    id = BigIntField(pk=True)
    bank: ForeignKeyRelation['PaymentAccount'] = ForeignKeyField('bot.Bank', on_delete=OnDelete.CASCADE, related_name="payment_accounts")
    transactions: ReverseRelation['Transaction']
    number = BigIntField()
    currency = CharField(max_length=10)


class Transaction(Model):
    id = BigIntField(pk=True)
    p_account: ForeignKeyRelation['PaymentAccount'] = ForeignKeyField('bot.PaymentAccount', on_delete=OnDelete.CASCADE, related_name="transactions")
    trxn_id = CharField(max_length=40)
    amount = BigIntField()
    type = CharEnumField(enum_type=enums.TransactionType, max_length=20)