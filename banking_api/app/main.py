from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated
from uuid import UUID, uuid4

import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, Query, status

from app.database import get_db, init_db, write_transaction
from app.schemas import AccountCreate, AccountRead, MoneyOperation, TransactionRead, TransferCreate


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="API Bancária Assíncrona",
    description=(
        "API didática para gerenciamento de contas, depósitos, saques, "
        "transferências e extratos. Valores são armazenados em centavos inteiros."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

DbSession = Annotated[aiosqlite.Connection, Depends(get_db)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def money_to_cents(amount: Decimal) -> int:
    return int(amount * 100)


def cents_to_money(cents: int) -> Decimal:
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))


def account_from_row(row: aiosqlite.Row) -> AccountRead:
    return AccountRead(
        id=UUID(row["id"]),
        holder_name=row["holder_name"],
        balance=cents_to_money(row["balance_cents"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def transaction_from_row(row: aiosqlite.Row) -> TransactionRead:
    return TransactionRead(
        id=UUID(row["id"]),
        operation_id=UUID(row["operation_id"]),
        account_id=UUID(row["account_id"]),
        transaction_type=row["transaction_type"],
        amount=cents_to_money(row["amount_cents"]),
        counterparty_account_id=(
            UUID(row["counterparty_account_id"])
            if row["counterparty_account_id"]
            else None
        ),
        description=row["description"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


async def find_account(db: aiosqlite.Connection, account_id: UUID) -> aiosqlite.Row:
    cursor = await db.execute(
        "SELECT id, holder_name, balance_cents, created_at FROM accounts WHERE id = ?",
        (str(account_id),),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    return row


async def insert_ledger_entry(
    db: aiosqlite.Connection,
    *,
    operation_id: UUID,
    account_id: UUID,
    transaction_type: str,
    amount_cents: int,
    counterparty_account_id: UUID | None = None,
    description: str | None = None,
) -> None:
    await db.execute(
        """
        INSERT INTO transactions (
            id, operation_id, account_id, transaction_type, amount_cents,
            counterparty_account_id, description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            str(operation_id),
            str(account_id),
            transaction_type,
            amount_cents,
            str(counterparty_account_id) if counterparty_account_id else None,
            description,
            utc_now(),
        ),
    )


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "message": "API bancária funcionando."}


@app.post(
    "/accounts",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Contas"],
    summary="Criar uma conta bancária",
)
async def create_account(payload: AccountCreate, db: DbSession):
    account_id = uuid4()
    created_at = utc_now()

    async with write_transaction(db):
        await db.execute(
            "INSERT INTO accounts (id, holder_name, balance_cents, created_at) VALUES (?, ?, 0, ?)",
            (str(account_id), payload.holder_name, created_at),
        )

    return AccountRead(
        id=account_id,
        holder_name=payload.holder_name,
        balance=Decimal("0.00"),
        created_at=datetime.fromisoformat(created_at),
    )


@app.get(
    "/accounts/{account_id}",
    response_model=AccountRead,
    tags=["Contas"],
    summary="Consultar conta e saldo",
)
async def get_account(account_id: UUID, db: DbSession):
    row = await find_account(db, account_id)
    return account_from_row(row)


@app.post(
    "/accounts/{account_id}/deposit",
    response_model=AccountRead,
    tags=["Operações"],
    summary="Depositar dinheiro",
)
async def deposit(account_id: UUID, payload: MoneyOperation, db: DbSession):
    amount_cents = money_to_cents(payload.amount)

    async with write_transaction(db):
        await find_account(db, account_id)
        await db.execute(
            "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
            (amount_cents, str(account_id)),
        )
        await insert_ledger_entry(
            db,
            operation_id=uuid4(),
            account_id=account_id,
            transaction_type="deposit",
            amount_cents=amount_cents,
            description=payload.description or "Depósito",
        )
        row = await find_account(db, account_id)

    return account_from_row(row)


@app.post(
    "/accounts/{account_id}/withdraw",
    response_model=AccountRead,
    tags=["Operações"],
    summary="Sacar dinheiro",
)
async def withdraw(account_id: UUID, payload: MoneyOperation, db: DbSession):
    amount_cents = money_to_cents(payload.amount)

    async with write_transaction(db):
        await find_account(db, account_id)
        cursor = await db.execute(
            """
            UPDATE accounts
            SET balance_cents = balance_cents - ?
            WHERE id = ? AND balance_cents >= ?
            """,
            (amount_cents, str(account_id), amount_cents),
        )
        updated = cursor.rowcount
        await cursor.close()
        if updated == 0:
            raise HTTPException(status_code=409, detail="Saldo insuficiente.")

        await insert_ledger_entry(
            db,
            operation_id=uuid4(),
            account_id=account_id,
            transaction_type="withdrawal",
            amount_cents=amount_cents,
            description=payload.description or "Saque",
        )
        row = await find_account(db, account_id)

    return account_from_row(row)


@app.post(
    "/accounts/{source_account_id}/transfers",
    response_model=AccountRead,
    tags=["Operações"],
    summary="Transferir dinheiro para outra conta",
)
async def transfer(
    source_account_id: UUID,
    payload: TransferCreate,
    db: DbSession,
):
    destination_id = payload.destination_account_id
    if source_account_id == destination_id:
        raise HTTPException(
            status_code=422,
            detail="A conta de origem e a conta de destino devem ser diferentes.",
        )

    amount_cents = money_to_cents(payload.amount)
    operation_id = uuid4()

    async with write_transaction(db):
        await find_account(db, source_account_id)
        await find_account(db, destination_id)

        cursor = await db.execute(
            """
            UPDATE accounts
            SET balance_cents = balance_cents - ?
            WHERE id = ? AND balance_cents >= ?
            """,
            (amount_cents, str(source_account_id), amount_cents),
        )
        debited = cursor.rowcount
        await cursor.close()
        if debited == 0:
            raise HTTPException(status_code=409, detail="Saldo insuficiente para realizar a transferência.")

        await db.execute(
            "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
            (amount_cents, str(destination_id)),
        )

        description = payload.description or "Transferência bancária"
        await insert_ledger_entry(
            db,
            operation_id=operation_id,
            account_id=source_account_id,
            transaction_type="transfer_sent",
            amount_cents=amount_cents,
            counterparty_account_id=destination_id,
            description=description,
        )
        await insert_ledger_entry(
            db,
            operation_id=operation_id,
            account_id=destination_id,
            transaction_type="transfer_received",
            amount_cents=amount_cents,
            counterparty_account_id=source_account_id,
            description=description,
        )
        row = await find_account(db, source_account_id)

    return account_from_row(row)


@app.get(
    "/accounts/{account_id}/transactions",
    response_model=list[TransactionRead],
    tags=["Extrato"],
    summary="Consultar extrato da conta",
)
async def get_transactions(
    account_id: UUID,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    await find_account(db, account_id)
    cursor = await db.execute(
        """
        SELECT id, operation_id, account_id, transaction_type, amount_cents,
               counterparty_account_id, description, created_at
        FROM transactions
        WHERE account_id = ?
        ORDER BY created_at DESC, rowid DESC
        LIMIT ? OFFSET ?
        """,
        (str(account_id), limit, offset),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [transaction_from_row(row) for row in rows]
