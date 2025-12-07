"""
Banking domain logic with Design-by-Contract enforcement.

This module implements a BankAccount class with:
- Preconditions (validated before method execution)
- Postconditions (validated after method execution)
- Class invariants (validated after every public method)
"""

from typing import Union
import icontract


@icontract.invariant(lambda self: self.balance >= 0, "Balance must never be negative")
class BankAccount:
    """
    A bank account with Design-by-Contract validation.
    
    Invariant:
        - balance >= 0 (enforced after every method call)
    
    Attributes:
        account_id: Unique identifier for the account
        balance: Current account balance (must be >= 0)
    """
    
    def __init__(self, account_id: str, initial_balance: Union[int, float] = 0) -> None:
        """
        Initialize a new bank account.
        
        Args:
            account_id: Unique identifier for this account
            initial_balance: Starting balance (default: 0)
        
        Raises:
            icontract.ViolationError: If initial_balance < 0
        """
        if initial_balance < 0:
            raise icontract.ViolationError("Initial balance must be >= 0")
        self.account_id = account_id
        self._balance: Union[int, float] = initial_balance
    
    @property
    def balance(self) -> Union[int, float]:
        """Get the current account balance."""
        return self._balance
    
    @icontract.require(lambda amount: amount > 0, "Deposit amount must be positive")
    @icontract.snapshot(lambda self: self.balance, name="old_balance")
    @icontract.ensure(
        lambda self, OLD, amount: self.balance == OLD.old_balance + amount,
        "Balance must increase by exactly the deposit amount"
    )
    def deposit(self, amount: Union[int, float]) -> None:
        """
        Deposit funds into the account.
        
        Preconditions:
            - amount > 0
        
        Postconditions:
            - balance == OLD.balance + amount
        
        Args:
            amount: Amount to deposit (must be positive)
        
        Raises:
            icontract.ViolationError: If preconditions or postconditions fail
        """
        self._balance += amount
    
    @icontract.require(lambda amount: amount > 0, "Withdrawal amount must be positive")
    @icontract.require(
        lambda self, amount: self.balance >= amount,
        "Insufficient funds for withdrawal"
    )
    @icontract.snapshot(lambda self: self.balance, name="old_balance")
    @icontract.ensure(
        lambda self, OLD, amount: self.balance == OLD.old_balance - amount,
        "Balance must decrease by exactly the withdrawal amount"
    )
    def withdraw(self, amount: Union[int, float]) -> None:
        """
        Withdraw funds from the account.
        
        Preconditions:
            - amount > 0
            - balance >= amount
        
        Postconditions:
            - balance == OLD.balance - amount
        
        Args:
            amount: Amount to withdraw (must be positive and <= balance)
        
        Raises:
            icontract.ViolationError: If preconditions or postconditions fail
        """
        self._balance -= amount
    
    @icontract.require(lambda self, other: self != other, "Cannot transfer to the same account")
    @icontract.require(lambda amount: amount > 0, "Transfer amount must be positive")
    @icontract.require(
        lambda self, amount: self.balance >= amount,
        "Insufficient funds for transfer"
    )
    @icontract.snapshot(lambda self: self.balance, name="self_balance")
    @icontract.snapshot(lambda other: other.balance, name="other_balance")
    @icontract.ensure(
        lambda self, OLD, amount: self.balance == OLD.self_balance - amount,
        "Source balance must decrease by transfer amount"
    )
    @icontract.ensure(
        lambda other, OLD, amount: other.balance == OLD.other_balance + amount,
        "Destination balance must increase by transfer amount"
    )
    def transfer_to(self, other: "BankAccount", amount: Union[int, float]) -> None:
        """
        Transfer funds to another account.
        
        Preconditions:
            - self != other (cannot transfer to same account)
            - amount > 0
            - self.balance >= amount
        
        Postconditions:
            - self.balance == OLD.self_balance - amount
            - other.balance == OLD.other_balance + amount
        
        Args:
            other: Destination account
            amount: Amount to transfer (must be positive and <= balance)
        
        Raises:
            icontract.ViolationError: If preconditions or postconditions fail
        """
        self._balance -= amount
        other._balance += amount
    
    def __repr__(self) -> str:
        return f"BankAccount(id={self.account_id!r}, balance={self.balance})"
