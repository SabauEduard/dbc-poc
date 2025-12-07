"""
Unit tests for the BankAccount class.

Tests cover:
- Valid paths (normal usage)
- Invalid paths (contract violations)
- Edge cases
"""

import pytest
import icontract

from app.banking import BankAccount


class TestBankAccountCreation:
    """Tests for BankAccount initialization."""
    
    def test_create_account_with_zero_balance(self):
        """Account can be created with default zero balance."""
        account = BankAccount("acc-001")
        assert account.account_id == "acc-001"
        assert account.balance == 0
    
    def test_create_account_with_initial_balance(self):
        """Account can be created with positive initial balance."""
        account = BankAccount("acc-002", initial_balance=100)
        assert account.account_id == "acc-002"
        assert account.balance == 100
    
    def test_create_account_with_float_balance(self):
        """Account can be created with float balance."""
        account = BankAccount("acc-003", initial_balance=50.75)
        assert account.balance == 50.75
    
    def test_create_account_with_negative_balance_fails(self):
        """Creating account with negative balance violates contract."""
        with pytest.raises(icontract.ViolationError):
            BankAccount("acc-004", initial_balance=-100)


class TestDeposit:
    """Tests for the deposit method."""
    
    def test_deposit_positive_amount(self):
        """Depositing positive amount increases balance correctly."""
        account = BankAccount("acc-010", initial_balance=100)
        account.deposit(50)
        assert account.balance == 150
    
    def test_deposit_float_amount(self):
        """Depositing float amount works correctly."""
        account = BankAccount("acc-011", initial_balance=100)
        account.deposit(25.50)
        assert account.balance == 125.50
    
    def test_deposit_large_amount(self):
        """Depositing large amounts works correctly."""
        account = BankAccount("acc-012")
        account.deposit(1_000_000)
        assert account.balance == 1_000_000
    
    def test_deposit_tiny_amount(self):
        """Depositing tiny amounts works correctly."""
        account = BankAccount("acc-013")
        account.deposit(0.01)
        assert account.balance == 0.01
    
    def test_deposit_zero_fails(self):
        """Depositing zero amount violates precondition."""
        account = BankAccount("acc-014", initial_balance=100)
        with pytest.raises(icontract.ViolationError, match="must be positive"):
            account.deposit(0)
    
    def test_deposit_negative_fails(self):
        """Depositing negative amount violates precondition."""
        account = BankAccount("acc-015", initial_balance=100)
        with pytest.raises(icontract.ViolationError, match="must be positive"):
            account.deposit(-50)
    
    def test_deposit_multiple_times(self):
        """Multiple deposits accumulate correctly."""
        account = BankAccount("acc-016")
        account.deposit(100)
        account.deposit(50)
        account.deposit(25)
        assert account.balance == 175


class TestWithdraw:
    """Tests for the withdraw method."""
    
    def test_withdraw_positive_amount(self):
        """Withdrawing positive amount decreases balance correctly."""
        account = BankAccount("acc-020", initial_balance=100)
        account.withdraw(30)
        assert account.balance == 70
    
    def test_withdraw_float_amount(self):
        """Withdrawing float amount works correctly."""
        account = BankAccount("acc-021", initial_balance=100)
        account.withdraw(25.50)
        assert account.balance == 74.50
    
    def test_withdraw_exact_balance(self):
        """Withdrawing exact balance leaves zero balance."""
        account = BankAccount("acc-022", initial_balance=100)
        account.withdraw(100)
        assert account.balance == 0
    
    def test_withdraw_zero_fails(self):
        """Withdrawing zero amount violates precondition."""
        account = BankAccount("acc-023", initial_balance=100)
        with pytest.raises(icontract.ViolationError, match="must be positive"):
            account.withdraw(0)
    
    def test_withdraw_negative_fails(self):
        """Withdrawing negative amount violates precondition."""
        account = BankAccount("acc-024", initial_balance=100)
        with pytest.raises(icontract.ViolationError, match="must be positive"):
            account.withdraw(-50)
    
    def test_withdraw_more_than_balance_fails(self):
        """Withdrawing more than balance violates precondition."""
        account = BankAccount("acc-025", initial_balance=100)
        with pytest.raises(icontract.ViolationError, match="Insufficient funds"):
            account.withdraw(150)
    
    def test_withdraw_from_zero_balance_fails(self):
        """Withdrawing from zero balance violates precondition."""
        account = BankAccount("acc-026", initial_balance=0)
        with pytest.raises(icontract.ViolationError, match="Insufficient funds"):
            account.withdraw(1)
    
    def test_withdraw_multiple_times(self):
        """Multiple withdrawals work correctly."""
        account = BankAccount("acc-027", initial_balance=100)
        account.withdraw(30)
        account.withdraw(20)
        account.withdraw(10)
        assert account.balance == 40


class TestTransfer:
    """Tests for the transfer_to method."""
    
    def test_transfer_positive_amount(self):
        """Transferring positive amount moves funds correctly."""
        account1 = BankAccount("acc-030", initial_balance=100)
        account2 = BankAccount("acc-031", initial_balance=50)
        
        account1.transfer_to(account2, 30)
        
        assert account1.balance == 70
        assert account2.balance == 80
    
    def test_transfer_float_amount(self):
        """Transferring float amount works correctly."""
        account1 = BankAccount("acc-032", initial_balance=100)
        account2 = BankAccount("acc-033", initial_balance=0)
        
        account1.transfer_to(account2, 25.50)
        
        assert account1.balance == 74.50
        assert account2.balance == 25.50
    
    def test_transfer_exact_balance(self):
        """Transferring exact balance leaves source at zero."""
        account1 = BankAccount("acc-034", initial_balance=100)
        account2 = BankAccount("acc-035", initial_balance=0)
        
        account1.transfer_to(account2, 100)
        
        assert account1.balance == 0
        assert account2.balance == 100
    
    def test_transfer_preserves_total(self):
        """Total system balance remains constant after transfer."""
        account1 = BankAccount("acc-036", initial_balance=100)
        account2 = BankAccount("acc-037", initial_balance=50)
        
        total_before = account1.balance + account2.balance
        account1.transfer_to(account2, 30)
        total_after = account1.balance + account2.balance
        
        assert total_before == total_after
    
    def test_transfer_zero_fails(self):
        """Transferring zero amount violates precondition."""
        account1 = BankAccount("acc-038", initial_balance=100)
        account2 = BankAccount("acc-039", initial_balance=0)
        
        with pytest.raises(icontract.ViolationError, match="must be positive"):
            account1.transfer_to(account2, 0)
    
    def test_transfer_negative_fails(self):
        """Transferring negative amount violates precondition."""
        account1 = BankAccount("acc-040", initial_balance=100)
        account2 = BankAccount("acc-041", initial_balance=0)
        
        with pytest.raises(icontract.ViolationError, match="must be positive"):
            account1.transfer_to(account2, -50)
    
    def test_transfer_to_same_account_fails(self):
        """Transferring to same account violates precondition."""
        account = BankAccount("acc-042", initial_balance=100)
        
        with pytest.raises(icontract.ViolationError, match="same account"):
            account.transfer_to(account, 50)
    
    def test_transfer_more_than_balance_fails(self):
        """Transferring more than balance violates precondition."""
        account1 = BankAccount("acc-043", initial_balance=100)
        account2 = BankAccount("acc-044", initial_balance=0)
        
        with pytest.raises(icontract.ViolationError, match="Insufficient funds"):
            account1.transfer_to(account2, 150)
    
    def test_transfer_from_zero_balance_fails(self):
        """Transferring from zero balance violates precondition."""
        account1 = BankAccount("acc-045", initial_balance=0)
        account2 = BankAccount("acc-046", initial_balance=100)
        
        with pytest.raises(icontract.ViolationError, match="Insufficient funds"):
            account1.transfer_to(account2, 1)


class TestInvariant:
    """Tests for class invariant enforcement."""
    
    def test_invariant_maintained_after_deposit(self):
        """Balance >= 0 after deposit."""
        account = BankAccount("acc-050")
        account.deposit(100)
        assert account.balance >= 0
    
    def test_invariant_maintained_after_withdraw(self):
        """Balance >= 0 after withdraw."""
        account = BankAccount("acc-051", initial_balance=100)
        account.withdraw(100)
        assert account.balance >= 0
    
    def test_invariant_maintained_after_transfer(self):
        """Balance >= 0 for both accounts after transfer."""
        account1 = BankAccount("acc-052", initial_balance=100)
        account2 = BankAccount("acc-053", initial_balance=0)
        
        account1.transfer_to(account2, 100)
        
        assert account1.balance >= 0
        assert account2.balance >= 0


class TestRepr:
    """Tests for string representation."""
    
    def test_repr(self):
        """Account has readable string representation."""
        account = BankAccount("test-acc", initial_balance=123.45)
        repr_str = repr(account)
        
        assert "test-acc" in repr_str
        assert "123.45" in repr_str

