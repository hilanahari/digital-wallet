from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from app.database import init_db, get_connection

app = FastAPI()
init_db()
accounts = {}  # מסד נתונים זמני, המפתח הוא id
# והערך הוא החשבון כולו
next_id = 1  # המספר שיקבל החשבון הבא


class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    owner: str = Field(min_length=1, max_length=50)


class DepositCreate(BaseModel):
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
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    return accounts[account_id]


@app.post("/accounts/{account_id}/deposits")
def create_deposit(account_id: int, data: DepositCreate):
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")

    accounts[account_id]["balance"] += data.amount
    return accounts[account_id]
