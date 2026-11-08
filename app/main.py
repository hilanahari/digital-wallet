from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

app = FastAPI()
accounts = {}
next_id = 1


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
    global next_id
    account = {"id": next_id, "owner": data.owner, "balance": 0}
    accounts[next_id] = account
    next_id += 1
    return account


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
