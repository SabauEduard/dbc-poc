"""
FastAPI REST API for the banking service with DbC validation.

This module provides HTTP endpoints that wrap the banking logic
and uses fastapi-icontract to automatically enforce contracts and
include them in the OpenAPI specification.
"""

from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel, Field
import icontract
from fastapi_icontract import require, ensure

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


# Note: With fastapi-icontract, we don't need manual error handling.
# The library automatically maps contract violations to HTTP errors.
# However, we keep this for reference and potential custom error handling.
def handle_contract_violation(e: icontract.ViolationError, context: str) -> dict:
    """
    Custom error detail formatter for contract violations.

    This is now optional with fastapi-icontract, but can be used
    for custom error formatting if needed.
    """
    error_message = str(e)

    if "Insufficient funds" in error_message:
        return {
            "error": "insufficient_funds",
            "message": error_message,
            "context": context
        }
    elif "same account" in error_message:
        return {
            "error": "invalid_transfer",
            "message": error_message,
            "context": context
        }
    elif "must be positive" in error_message:
        return {
            "error": "invalid_amount",
            "message": error_message,
            "context": context
        }
    else:
        return {
            "error": "contract_violation",
            "message": error_message,
            "context": context
        }


@app.post("/deposit", response_model=AccountResponse)
@require(
    lambda request: request.amount > 0,
    status_code=422,
    description="Deposit amount must be positive"
)
async def deposit(request: DepositRequest) -> AccountResponse:
    """
    Deposit funds into an account.

    Creates the account if it doesn't exist.

    Contract validations (enforced by fastapi-icontract):
    - amount must be > 0 (precondition)
    """
    account = get_or_create_account(request.account_id)
    account.deposit(request.amount)
    return AccountResponse(
        account_id=account.account_id,
        balance=account.balance,
        message=f"Successfully deposited {request.amount}"
    )


@app.post("/withdraw", response_model=AccountResponse)
@require(
    lambda request: request.amount > 0,
    status_code=422,
    description="Withdrawal amount must be positive"
)
async def withdraw(request: WithdrawRequest) -> AccountResponse:
    """
    Withdraw funds from an account.

    Creates the account if it doesn't exist (will fail if withdrawing from zero balance).

    Contract validations (enforced by fastapi-icontract):
    - amount must be > 0 (precondition)
    - account must have sufficient funds (enforced by BankAccount.withdraw)
    """
    account = get_or_create_account(request.account_id)
    # The BankAccount.withdraw method has its own contracts that will be enforced
    try:
        account.withdraw(request.amount)
        return AccountResponse(
            account_id=account.account_id,
            balance=account.balance,
            message=f"Successfully withdrew {request.amount}"
        )
    except icontract.ViolationError as e:
        # Map specific contract violations to appropriate HTTP status codes
        error_msg = str(e)
        if "Insufficient funds" in error_msg:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail=handle_contract_violation(e, "withdraw"))
        raise


@app.post("/transfer", response_model=TransferResponse)
@require(
    lambda request: request.amount > 0,
    status_code=422,
    description="Transfer amount must be positive"
)
@require(
    lambda request: request.from_id != request.to_id,
    status_code=422,
    description="Cannot transfer to the same account"
)
async def transfer(request: TransferRequest) -> TransferResponse:
    """
    Transfer funds between accounts.

    Creates accounts if they don't exist.

    Contract validations (enforced by fastapi-icontract):
    - amount must be > 0 (precondition)
    - source and destination must be different accounts (precondition)
    - source account must have sufficient funds (enforced by BankAccount.transfer_to)
    """
    from_account = get_or_create_account(request.from_id)
    to_account = get_or_create_account(request.to_id)

    # The BankAccount.transfer_to method has its own contracts
    try:
        from_account.transfer_to(to_account, request.amount)
        return TransferResponse(
            from_account={"account_id": from_account.account_id, "balance": from_account.balance},
            to_account={"account_id": to_account.account_id, "balance": to_account.balance},
            message=f"Successfully transferred {request.amount} from {request.from_id} to {request.to_id}"
        )
    except icontract.ViolationError as e:
        # Map specific contract violations to appropriate HTTP status codes
        error_msg = str(e)
        if "Insufficient funds" in error_msg:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail=handle_contract_violation(e, "transfer"))
        raise


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


# ============================================================================
# FastAPI-icontract Integration
# ============================================================================
# This section integrates contracts into the OpenAPI specification and
# enhances the Swagger UI with contract visualization.

from fastapi_icontract import wrap_openapi_with_contracts

# Include contracts in the OpenAPI specification (/openapi.json)
# This makes contracts visible to API consumers and tools
wrap_openapi_with_contracts(app=app)

# Note: set_up_route_for_docs_with_contracts_plugin is available but optional
# It provides enhanced Swagger UI visualization of contracts
# Uncomment the following lines to enable it:
#
# from fastapi_icontract import set_up_route_for_docs_with_contracts_plugin
# set_up_route_for_docs_with_contracts_plugin(app=app)

