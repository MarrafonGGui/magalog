from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite

DB_PATH = Path(os.getenv("BANK_DB_PATH", "bank.db"))


async def open_db() -> aiosqlite.Connection:
    """Abre uma conexão SQLite configurada para operações assíncronas."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH, timeout=10)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("PRAGMA busy_timeout = 10000")
    return db


async def init_db() -> None:
    async with await open_db() as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                holder_name TEXT NOT NULL,
                balance_cents INTEGER NOT NULL DEFAULT 0
                    CHECK (balance_cents >= 0),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                operation_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK (
                    transaction_type IN (
                        'deposit', 'withdrawal', 'transfer_sent', 'transfer_received'
                    )
                ),
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                counterparty_account_id TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (counterparty_account_id) REFERENCES accounts(id)
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_account_created
                ON transactions(account_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_transactions_operation
                ON transactions(operation_id);
            """
        )
        await db.commit()


@asynccontextmanager
async def write_transaction(db: aiosqlite.Connection) -> AsyncIterator[None]:
    """Garante commit integral ou rollback de uma operação financeira."""
    await db.execute("BEGIN IMMEDIATE")
    try:
        yield
        await db.commit()
    except Exception:
        await db.rollback()
        raise


async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    db = await open_db()
    try:
        yield db
    finally:
        await db.close()
