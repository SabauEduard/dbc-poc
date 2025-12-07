"""
Property-based tests for the BankAccount class using Hypothesis.

These tests verify invariants and properties that should hold for
any valid input, letting Hypothesis discover edge cases automatically.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, Phase
import icontract

from app.banking import BankAccount


# Strategies for generating test data
positive_amounts = st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False)
non_positive_amounts = st.floats(max_value=0, allow_nan=False, allow_infinity=False)
initial_balances = st.floats(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False)
account_ids = st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N')))


class TestDepositProperties:
    """Property-based tests for deposit operation."""
    
    @given(initial=initial_balances, amount=positive_amounts)
    @settings(max_examples=100)
    def test_deposit_increases_balance_by_amount(self, initial: float, amount: float):
        """
        Property: For all positive amounts, balance increases by exactly that amount.
        
        ∀ initial ≥ 0, amount > 0:
            new_balance = initial + amount
        """
        account = BankAccount("prop-test", initial_balance=initial)
        old_balance = account.balance
        
        account.deposit(amount)
        
        assert account.balance == pytest.approx(old_balance + amount, rel=1e-9)
    
    @given(initial=initial_balances, amount=positive_amounts)
    @settings(max_examples=100)
    def test_deposit_preserves_non_negative_invariant(self, initial: float, amount: float):
        """
        Property: Balance remains non-negative after any valid deposit.
        
        ∀ initial ≥ 0, amount > 0:
            new_balance ≥ 0
        """
        account = BankAccount("prop-test", initial_balance=initial)
        account.deposit(amount)
        assert account.balance >= 0
    
    @given(initial=initial_balances, amount=non_positive_amounts)
    @settings(max_examples=50)
    def test_deposit_rejects_non_positive_amounts(self, initial: float, amount: float):
        """
        Property: Contract violation for non-positive deposit amounts.
        
        ∀ amount ≤ 0:
            deposit(amount) raises ViolationError
        """
        account = BankAccount("prop-test", initial_balance=initial)
        
        with pytest.raises(icontract.ViolationError):
            account.deposit(amount)
    
    @given(
        initial=initial_balances,
        amounts=st.lists(positive_amounts, min_size=1, max_size=10)
    )
    @settings(max_examples=50)
    def test_multiple_deposits_are_additive(self, initial: float, amounts: list):
        """
        Property: Multiple deposits sum correctly.
        
        ∀ amounts a1, a2, ..., an > 0:
            final_balance = initial + Σ(ai)
        """
        account = BankAccount("prop-test", initial_balance=initial)
        
        for amount in amounts:
            account.deposit(amount)
        
        expected = initial + sum(amounts)
        assert account.balance == pytest.approx(expected, rel=1e-9)


class TestWithdrawProperties:
    """Property-based tests for withdraw operation."""
    
    @given(initial=initial_balances, fraction=st.floats(min_value=0.01, max_value=1.0))
    @settings(max_examples=100)
    def test_withdraw_decreases_balance_by_amount(self, initial: float, fraction: float):
        """
        Property: For valid amounts, balance decreases by exactly that amount.
        
        ∀ initial > 0, amount ∈ (0, initial]:
            new_balance = initial - amount
        """
        assume(initial > 0.01)  # Need some balance to withdraw
        amount = initial * fraction  # Ensure amount <= initial
        assume(amount > 0)
        
        account = BankAccount("prop-test", initial_balance=initial)
        old_balance = account.balance
        
        account.withdraw(amount)
        
        assert account.balance == pytest.approx(old_balance - amount, rel=1e-9)
    
    @given(initial=initial_balances, fraction=st.floats(min_value=0.01, max_value=1.0))
    @settings(max_examples=100)
    def test_withdraw_preserves_non_negative_invariant(self, initial: float, fraction: float):
        """
        Property: Balance remains non-negative after any valid withdrawal.
        
        ∀ valid withdrawal:
            new_balance ≥ 0
        """
        assume(initial > 0.01)
        amount = initial * fraction
        assume(amount > 0)
        
        account = BankAccount("prop-test", initial_balance=initial)
        account.withdraw(amount)
        
        assert account.balance >= 0
    
    @given(initial=initial_balances, excess=st.floats(min_value=0.01, max_value=1000))
    @settings(max_examples=50)
    def test_withdraw_rejects_amounts_exceeding_balance(self, initial: float, excess: float):
        """
        Property: Contract violation when withdrawing more than balance.
        
        ∀ amount > balance:
            withdraw(amount) raises ViolationError
        """
        account = BankAccount("prop-test", initial_balance=initial)
        amount = initial + excess  # Always exceeds balance
        
        with pytest.raises(icontract.ViolationError):
            account.withdraw(amount)
    
    @given(initial=initial_balances, amount=non_positive_amounts)
    @settings(max_examples=50)
    def test_withdraw_rejects_non_positive_amounts(self, initial: float, amount: float):
        """
        Property: Contract violation for non-positive withdrawal amounts.
        
        ∀ amount ≤ 0:
            withdraw(amount) raises ViolationError
        """
        account = BankAccount("prop-test", initial_balance=initial)
        
        with pytest.raises(icontract.ViolationError):
            account.withdraw(amount)


class TestTransferProperties:
    """Property-based tests for transfer operation."""
    
    @given(
        balance1=initial_balances,
        balance2=initial_balances,
        fraction=st.floats(min_value=0.01, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_transfer_preserves_total_balance(self, balance1: float, balance2: float, fraction: float):
        """
        Property: Total system balance is conserved during transfer.
        
        ∀ valid transfers:
            old_balance1 + old_balance2 = new_balance1 + new_balance2
        """
        assume(balance1 > 0.01)  # Need balance to transfer
        amount = balance1 * fraction
        assume(amount > 0)
        
        account1 = BankAccount("sender", initial_balance=balance1)
        account2 = BankAccount("receiver", initial_balance=balance2)
        
        total_before = account1.balance + account2.balance
        account1.transfer_to(account2, amount)
        total_after = account1.balance + account2.balance
        
        assert total_before == pytest.approx(total_after, rel=1e-9)
    
    @given(
        balance1=initial_balances,
        balance2=initial_balances,
        fraction=st.floats(min_value=0.01, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_transfer_correct_amounts(self, balance1: float, balance2: float, fraction: float):
        """
        Property: Source decreases and destination increases by transfer amount.
        
        ∀ valid transfers:
            new_source = old_source - amount
            new_dest = old_dest + amount
        """
        assume(balance1 > 0.01)
        amount = balance1 * fraction
        assume(amount > 0)
        
        account1 = BankAccount("sender", initial_balance=balance1)
        account2 = BankAccount("receiver", initial_balance=balance2)
        
        old_balance1 = account1.balance
        old_balance2 = account2.balance
        
        account1.transfer_to(account2, amount)
        
        assert account1.balance == pytest.approx(old_balance1 - amount, rel=1e-9)
        assert account2.balance == pytest.approx(old_balance2 + amount, rel=1e-9)
    
    @given(
        balance1=initial_balances,
        balance2=initial_balances,
        fraction=st.floats(min_value=0.01, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_transfer_preserves_invariants(self, balance1: float, balance2: float, fraction: float):
        """
        Property: Both accounts maintain non-negative balance after transfer.
        
        ∀ valid transfers:
            source.balance ≥ 0 ∧ dest.balance ≥ 0
        """
        assume(balance1 > 0.01)
        amount = balance1 * fraction
        assume(amount > 0)
        
        account1 = BankAccount("sender", initial_balance=balance1)
        account2 = BankAccount("receiver", initial_balance=balance2)
        
        account1.transfer_to(account2, amount)
        
        assert account1.balance >= 0
        assert account2.balance >= 0
    
    @given(balance=initial_balances, amount=positive_amounts)
    @settings(max_examples=50)
    def test_transfer_to_self_fails(self, balance: float, amount: float):
        """
        Property: Transfer to self always fails.
        
        ∀ accounts, amounts:
            account.transfer_to(account, amount) raises ViolationError
        """
        account = BankAccount("self-transfer", initial_balance=balance)
        
        with pytest.raises(icontract.ViolationError):
            account.transfer_to(account, amount)
    
    @given(
        balance1=initial_balances,
        balance2=initial_balances,
        excess=st.floats(min_value=0.01, max_value=1000)
    )
    @settings(max_examples=50)
    def test_transfer_exceeding_balance_fails(self, balance1: float, balance2: float, excess: float):
        """
        Property: Transfer fails when amount exceeds source balance.
        
        ∀ amount > source.balance:
            transfer(dest, amount) raises ViolationError
        """
        account1 = BankAccount("sender", initial_balance=balance1)
        account2 = BankAccount("receiver", initial_balance=balance2)
        
        amount = balance1 + excess  # Always exceeds balance
        
        with pytest.raises(icontract.ViolationError):
            account1.transfer_to(account2, amount)


class TestCompositeOperations:
    """Property tests for sequences of operations."""
    
    @given(
        initial=initial_balances,
        deposits=st.lists(positive_amounts, min_size=0, max_size=5),
        withdraw_fractions=st.lists(
            st.floats(min_value=0.01, max_value=0.3),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=50, phases=[Phase.generate, Phase.target])
    def test_sequence_of_operations_maintains_invariant(
        self, initial: float, deposits: list, withdraw_fractions: list
    ):
        """
        Property: Any valid sequence of operations maintains balance ≥ 0.
        """
        account = BankAccount("sequence-test", initial_balance=initial)
        
        # Perform deposits
        for amount in deposits:
            account.deposit(amount)
            assert account.balance >= 0
        
        # Perform withdrawals (as fractions of current balance)
        for fraction in withdraw_fractions:
            if account.balance > 0.01:
                amount = account.balance * fraction
                if amount > 0:
                    account.withdraw(amount)
                    assert account.balance >= 0
    
    @given(
        balances=st.lists(
            initial_balances,
            min_size=2,
            max_size=5
        ),
        transfer_specs=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=4),  # from index
                st.integers(min_value=0, max_value=4),  # to index
                st.floats(min_value=0.01, max_value=0.5)  # fraction
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=30, phases=[Phase.generate])
    def test_multiple_transfers_preserve_total(self, balances: list, transfer_specs: list):
        """
        Property: Multiple transfers preserve total system balance.
        
        ∀ sequences of valid transfers:
            Σ(initial_balances) = Σ(final_balances)
        """
        n = len(balances)
        accounts = [
            BankAccount(f"acc-{i}", initial_balance=bal)
            for i, bal in enumerate(balances)
        ]
        
        total_before = sum(acc.balance for acc in accounts)
        
        for from_idx, to_idx, fraction in transfer_specs:
            # Normalize indices to valid range
            from_idx = from_idx % n
            to_idx = to_idx % n
            
            if from_idx == to_idx:
                continue  # Skip self-transfers
            
            source = accounts[from_idx]
            if source.balance > 0.01:
                amount = source.balance * fraction
                if amount > 0:
                    try:
                        source.transfer_to(accounts[to_idx], amount)
                    except icontract.ViolationError:
                        pass  # Skip invalid transfers
        
        total_after = sum(acc.balance for acc in accounts)
        
        assert total_before == pytest.approx(total_after, rel=1e-9)

