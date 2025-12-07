"""
FastAPI REST API for the banking service with DbC validation.

This module provides HTTP endpoints that wrap the banking logic
and map contract violations to appropriate HTTP error responses.
"""

from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import icontract

from .banking import BankAccount


# In-memory storage for accounts (for demo purposes)
accounts: Dict[str, BankAccount] = {}


def get_or_create_account(account_id: str) -> BankAccount:
    """Get an existing account or create a new one with zero balance."""
    if account_id not in accounts:
        accounts[account_id] = BankAccount(account_id, initial_balance=0)
    return accounts[account_id]


# Pydantic models for request validation
class DepositRequest(BaseModel):
    """Request body for deposit endpoint."""
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., description="Amount to deposit")


class WithdrawRequest(BaseModel):
    """Request body for withdraw endpoint."""
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., description="Amount to withdraw")


class TransferRequest(BaseModel):
    """Request body for transfer endpoint."""
    from_id: str = Field(..., description="Source account identifier")
    to_id: str = Field(..., description="Destination account identifier")
    amount: float = Field(..., description="Amount to transfer")


class AccountResponse(BaseModel):
    """Response body containing account information."""
    account_id: str
    balance: float
    message: str


class TransferResponse(BaseModel):
    """Response body for transfer operations."""
    from_account: dict
    to_account: dict
    message: str


# Create FastAPI application
app = FastAPI(
    title="Banking Service API",
    description="A banking service demonstrating Design-by-Contract with FastAPI",
    version="1.0.0",
)


def handle_contract_violation(e: icontract.ViolationError, context: str) -> HTTPException:
    """
    Map icontract violations to appropriate HTTP errors.
    
    - Precondition failures related to amounts -> 422 (Unprocessable Entity)
    - Precondition failures related to insufficient funds -> 409 (Conflict)
    - Other violations -> 400 (Bad Request)
    """
    error_message = str(e)
    
    if "Insufficient funds" in error_message:
        return HTTPException(status_code=409, detail={
            "error": "insufficient_funds",
            "message": error_message,
            "context": context
        })
    elif "same account" in error_message:
        return HTTPException(status_code=422, detail={
            "error": "invalid_transfer",
            "message": error_message,
            "context": context
        })
    elif "must be positive" in error_message:
        return HTTPException(status_code=422, detail={
            "error": "invalid_amount",
            "message": error_message,
            "context": context
        })
    else:
        return HTTPException(status_code=400, detail={
            "error": "contract_violation",
            "message": error_message,
            "context": context
        })


@app.post("/deposit", response_model=AccountResponse)
async def deposit(request: DepositRequest) -> AccountResponse:
    """
    Deposit funds into an account.
    
    Creates the account if it doesn't exist.
    
    Contract validations:
    - amount must be > 0
    """
    try:
        account = get_or_create_account(request.account_id)
        account.deposit(request.amount)
        return AccountResponse(
            account_id=account.account_id,
            balance=account.balance,
            message=f"Successfully deposited {request.amount}"
        )
    except icontract.ViolationError as e:
        raise handle_contract_violation(e, "deposit")


@app.post("/withdraw", response_model=AccountResponse)
async def withdraw(request: WithdrawRequest) -> AccountResponse:
    """
    Withdraw funds from an account.
    
    Creates the account if it doesn't exist (will fail if withdrawing from zero balance).
    
    Contract validations:
    - amount must be > 0
    - account must have sufficient funds
    """
    try:
        account = get_or_create_account(request.account_id)
        account.withdraw(request.amount)
        return AccountResponse(
            account_id=account.account_id,
            balance=account.balance,
            message=f"Successfully withdrew {request.amount}"
        )
    except icontract.ViolationError as e:
        raise handle_contract_violation(e, "withdraw")


@app.post("/transfer", response_model=TransferResponse)
async def transfer(request: TransferRequest) -> TransferResponse:
    """
    Transfer funds between accounts.
    
    Creates accounts if they don't exist.
    
    Contract validations:
    - amount must be > 0
    - source and destination must be different accounts
    - source account must have sufficient funds
    """
    try:
        from_account = get_or_create_account(request.from_id)
        to_account = get_or_create_account(request.to_id)
        from_account.transfer_to(to_account, request.amount)
        return TransferResponse(
            from_account={"account_id": from_account.account_id, "balance": from_account.balance},
            to_account={"account_id": to_account.account_id, "balance": to_account.balance},
            message=f"Successfully transferred {request.amount} from {request.from_id} to {request.to_id}"
        )
    except icontract.ViolationError as e:
        raise handle_contract_violation(e, "transfer")


@app.get("/account/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str) -> AccountResponse:
    """
    Get account information.
    
    Creates the account if it doesn't exist (with zero balance).
    """
    account = get_or_create_account(account_id)
    return AccountResponse(
        account_id=account.account_id,
        balance=account.balance,
        message="Account retrieved successfully"
    )


@app.delete("/accounts")
async def clear_accounts() -> dict:
    """
    Clear all accounts (for testing purposes).
    """
    accounts.clear()
    return {"message": "All accounts cleared"}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "banking-api"}

