from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccountCreate(BaseModel):
    holder_name: str = Field(min_length=3, max_length=120, examples=["Maria da Silva"])

    @field_validator("holder_name")
    @classmethod
    def clean_holder_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 3:
            raise ValueError("O nome do titular deve ter ao menos 3 caracteres.")
        return value


class MoneyOperation(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
        examples=[150.00],
        description="Valor em reais. Deve ser maior que zero e ter no máximo 2 casas decimais.",
    )
    description: str | None = Field(default=None, max_length=140)


class TransferCreate(MoneyOperation):
    destination_account_id: UUID


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    holder_name: str
    balance: Decimal
    created_at: datetime


class TransactionRead(BaseModel):
    id: UUID
    operation_id: UUID
    account_id: UUID
    transaction_type: Literal["deposit", "withdrawal", "transfer_sent", "transfer_received"]
    amount: Decimal
    counterparty_account_id: UUID | None
    description: str | None
    created_at: datetime
