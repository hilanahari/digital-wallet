from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from app.database import init_db, get_connection

app = FastAPI()
init_db()


class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    owner: str = Field(min_length=1, max_length=50)


class DepositCreate(BaseModel):
    amount: int = Field(gt=0, strict=True)


class TransferCreate(BaseModel):
    from_account_id: int = Field(gt=0, strict=True)
    to_account_id: int = Field(gt=0, strict=True)
    amount: int = Field(gt=0, strict=True)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/accounts", status_code=201)
def create_account(data: AccountCreate):
    conn = get_connection()
    cur = conn.execute("INSERT INTO accounts (owner) VALUES (?)", (data.owner,))
    conn.commit()
    row = conn.execute(
        "SELECT id, owner, balance FROM accounts WHERE id = ?", (cur.lastrowid,)
    ).fetchone()  # רק שורה אחת
    conn.close()
    return dict(row)


@app.get("/accounts/{account_id}")
def get_account(account_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, owner, balance FROM accounts where id = ?", (account_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return dict(row)


@app.post("/accounts/{account_id}/deposits")
def create_deposit(account_id: int, data: DepositCreate):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, owner, balance FROM accounts where id = ?", (account_id,)
    ).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")

    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (data.amount, account_id),
    )

    ret = conn.execute(
        "SELECT id, owner, balance FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(ret)


@app.post("/transfers")
def create_transfer(data: TransferCreate):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE accounts SET balance = balance - ? where id = ?",
            (data.amount, data.from_account_id),
        )
        conn.execute(
            "UPDATE accounts SET balance = balance + ? where id = ?",
            (data.amount, data.to_account_id),
        )

        conn.execute(
            "INSERT INTO transactions (account_id, counterparty_id, type, amount) VALUES (?, ?, 'transfer_out', ?)",
            (data.from_account_id, data.to_account_id, -data.amount),
        )

        conn.execute(
            "INSERT INTO transactions (account_id, counterparty_id, type, amount) VALUES (?, ?, 'transfer_in', ?)",
            (data.to_account_id, data.from_account_id, data.amount),
        )

        ret = conn.execute(
            "SELECT id, owner, balance FROM accounts WHERE id = ?",
            (data.from_account_id,),
        ).fetchone()

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return dict(ret)
