"""
Integration tests for the FastAPI banking service.

Tests verify:
- Valid requests succeed
- Invalid requests trigger contract exceptions
- Appropriate HTTP status codes for different errors
- Consistent error response format
"""

import pytest
from fastapi.testclient import TestClient

from app.api import app, accounts


@pytest.fixture(autouse=True)
def clear_accounts():
    """Clear all accounts before each test."""
    accounts.clear()
    yield
    accounts.clear()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Health check endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestDepositEndpoint:
    """Tests for POST /deposit endpoint."""
    
    def test_deposit_creates_account_and_deposits(self, client):
        """Depositing to new account creates it with deposited amount."""
        response = client.post(
            "/deposit",
            json={"account_id": "acc-001", "amount": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "acc-001"
        assert data["balance"] == 100
        assert "Successfully deposited" in data["message"]
    
    def test_deposit_to_existing_account(self, client):
        """Depositing to existing account increases balance."""
        # First deposit
        client.post("/deposit", json={"account_id": "acc-002", "amount": 100})
        
        # Second deposit
        response = client.post(
            "/deposit",
            json={"account_id": "acc-002", "amount": 50}
        )
        
        assert response.status_code == 200
        assert response.json()["balance"] == 150
    
    def test_deposit_float_amount(self, client):
        """Depositing float amount works correctly."""
        response = client.post(
            "/deposit",
            json={"account_id": "acc-003", "amount": 99.99}
        )
        
        assert response.status_code == 200
        assert response.json()["balance"] == 99.99
    
    def test_deposit_zero_returns_422(self, client):
        """Depositing zero amount returns 422 Unprocessable Entity."""
        response = client.post(
            "/deposit",
            json={"account_id": "acc-004", "amount": 0}
        )
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "invalid_amount"
    
    def test_deposit_negative_returns_422(self, client):
        """Depositing negative amount returns 422 Unprocessable Entity."""
        response = client.post(
            "/deposit",
            json={"account_id": "acc-005", "amount": -50}
        )
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "invalid_amount"
    
    def test_deposit_missing_fields_returns_422(self, client):
        """Missing required fields return 422."""
        response = client.post("/deposit", json={"account_id": "acc-006"})
        assert response.status_code == 422


class TestWithdrawEndpoint:
    """Tests for POST /withdraw endpoint."""
    
    def test_withdraw_from_account_with_funds(self, client):
        """Withdrawing from account with sufficient funds succeeds."""
        # Setup: deposit first
        client.post("/deposit", json={"account_id": "acc-010", "amount": 100})
        
        # Withdraw
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-010", "amount": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 70
        assert "Successfully withdrew" in data["message"]
    
    def test_withdraw_exact_balance(self, client):
        """Withdrawing exact balance leaves zero balance."""
        client.post("/deposit", json={"account_id": "acc-011", "amount": 100})
        
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-011", "amount": 100}
        )
        
        assert response.status_code == 200
        assert response.json()["balance"] == 0
    
    def test_withdraw_more_than_balance_returns_409(self, client):
        """Withdrawing more than balance returns 409 Conflict."""
        client.post("/deposit", json={"account_id": "acc-012", "amount": 100})
        
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-012", "amount": 150}
        )
        
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["error"] == "insufficient_funds"
    
    def test_withdraw_from_zero_balance_returns_409(self, client):
        """Withdrawing from zero balance account returns 409."""
        # Create account with zero balance via GET
        client.get("/account/acc-013")
        
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-013", "amount": 50}
        )
        
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["error"] == "insufficient_funds"
    
    def test_withdraw_zero_returns_422(self, client):
        """Withdrawing zero amount returns 422."""
        client.post("/deposit", json={"account_id": "acc-014", "amount": 100})
        
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-014", "amount": 0}
        )
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "invalid_amount"
    
    def test_withdraw_negative_returns_422(self, client):
        """Withdrawing negative amount returns 422."""
        client.post("/deposit", json={"account_id": "acc-015", "amount": 100})
        
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-015", "amount": -50}
        )
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "invalid_amount"


class TestTransferEndpoint:
    """Tests for POST /transfer endpoint."""
    
    def test_transfer_between_accounts(self, client):
        """Transferring between accounts with sufficient funds succeeds."""
        # Setup
        client.post("/deposit", json={"account_id": "acc-020", "amount": 100})
        client.post("/deposit", json={"account_id": "acc-021", "amount": 50})
        
        # Transfer
        response = client.post(
            "/transfer",
            json={"from_id": "acc-020", "to_id": "acc-021", "amount": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["from_account"]["balance"] == 70
        assert data["to_account"]["balance"] == 80
        assert "Successfully transferred" in data["message"]
    
    def test_transfer_preserves_total(self, client):
        """Total balance is preserved after transfer."""
        client.post("/deposit", json={"account_id": "acc-022", "amount": 100})
        client.post("/deposit", json={"account_id": "acc-023", "amount": 50})
        
        response = client.post(
            "/transfer",
            json={"from_id": "acc-022", "to_id": "acc-023", "amount": 30}
        )
        
        data = response.json()
        total = data["from_account"]["balance"] + data["to_account"]["balance"]
        assert total == 150  # 100 + 50
    
    def test_transfer_exact_balance(self, client):
        """Transferring exact balance leaves source at zero."""
        client.post("/deposit", json={"account_id": "acc-024", "amount": 100})
        client.get("/account/acc-025")  # Create empty account
        
        response = client.post(
            "/transfer",
            json={"from_id": "acc-024", "to_id": "acc-025", "amount": 100}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["from_account"]["balance"] == 0
        assert data["to_account"]["balance"] == 100
    
    def test_transfer_to_same_account_returns_422(self, client):
        """Transferring to same account returns 422."""
        client.post("/deposit", json={"account_id": "acc-026", "amount": 100})
        
        response = client.post(
            "/transfer",
            json={"from_id": "acc-026", "to_id": "acc-026", "amount": 30}
        )
        
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "invalid_transfer"
    
    def test_transfer_more_than_balance_returns_409(self, client):
        """Transferring more than balance returns 409."""
        client.post("/deposit", json={"account_id": "acc-027", "amount": 100})
        client.get("/account/acc-028")
        
        response = client.post(
            "/transfer",
            json={"from_id": "acc-027", "to_id": "acc-028", "amount": 150}
        )
        
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["error"] == "insufficient_funds"
    
    def test_transfer_zero_returns_422(self, client):
        """Transferring zero amount returns 422."""
        client.post("/deposit", json={"account_id": "acc-029", "amount": 100})
        client.get("/account/acc-030")
        
        response = client.post(
            "/transfer",
            json={"from_id": "acc-029", "to_id": "acc-030", "amount": 0}
        )
        
        assert response.status_code == 422
    
    def test_transfer_negative_returns_422(self, client):
        """Transferring negative amount returns 422."""
        client.post("/deposit", json={"account_id": "acc-031", "amount": 100})
        client.get("/account/acc-032")
        
        response = client.post(
            "/transfer",
            json={"from_id": "acc-031", "to_id": "acc-032", "amount": -30}
        )
        
        assert response.status_code == 422


class TestAccountEndpoint:
    """Tests for GET /account/{account_id} endpoint."""
    
    def test_get_existing_account(self, client):
        """Getting existing account returns correct balance."""
        client.post("/deposit", json={"account_id": "acc-040", "amount": 100})
        
        response = client.get("/account/acc-040")
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "acc-040"
        assert data["balance"] == 100
    
    def test_get_nonexistent_account_creates_it(self, client):
        """Getting nonexistent account creates it with zero balance."""
        response = client.get("/account/acc-041")
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "acc-041"
        assert data["balance"] == 0


class TestClearAccountsEndpoint:
    """Tests for DELETE /accounts endpoint."""
    
    def test_clear_accounts(self, client):
        """Clearing accounts removes all accounts."""
        # Setup
        client.post("/deposit", json={"account_id": "acc-050", "amount": 100})
        client.post("/deposit", json={"account_id": "acc-051", "amount": 200})
        
        # Clear
        response = client.delete("/accounts")
        assert response.status_code == 200
        
        # Verify accounts are cleared (new accounts start at 0)
        response = client.get("/account/acc-050")
        assert response.json()["balance"] == 0


class TestErrorResponseFormat:
    """Tests to verify consistent error response format."""
    
    def test_contract_violation_includes_context(self, client):
        """Contract violations include operation context."""
        response = client.post(
            "/deposit",
            json={"account_id": "acc-060", "amount": -100}
        )
        
        detail = response.json()["detail"]
        assert "context" in detail
        assert detail["context"] == "deposit"
    
    def test_error_includes_message(self, client):
        """Error responses include descriptive message."""
        client.post("/deposit", json={"account_id": "acc-061", "amount": 100})
        
        response = client.post(
            "/withdraw",
            json={"account_id": "acc-061", "amount": 200}
        )
        
        detail = response.json()["detail"]
        assert "message" in detail
        assert len(detail["message"]) > 0


class TestIntegrationScenarios:
    """End-to-end integration scenarios."""
    
    def test_full_banking_workflow(self, client):
        """Complete banking workflow: create accounts, deposit, transfer, withdraw."""
        # Create accounts with deposits
        client.post("/deposit", json={"account_id": "alice", "amount": 1000})
        client.post("/deposit", json={"account_id": "bob", "amount": 500})
        
        # Alice transfers to Bob
        client.post("/transfer", json={"from_id": "alice", "to_id": "bob", "amount": 200})
        
        # Bob withdraws
        client.post("/withdraw", json={"account_id": "bob", "amount": 100})
        
        # Verify final state
        alice = client.get("/account/alice").json()
        bob = client.get("/account/bob").json()
        
        assert alice["balance"] == 800  # 1000 - 200
        assert bob["balance"] == 600    # 500 + 200 - 100
    
    def test_multiple_transfers_maintain_total(self, client):
        """Multiple transfers maintain total system balance."""
        # Setup initial state
        client.post("/deposit", json={"account_id": "a", "amount": 100})
        client.post("/deposit", json={"account_id": "b", "amount": 100})
        client.post("/deposit", json={"account_id": "c", "amount": 100})
        
        initial_total = 300
        
        # Perform multiple transfers
        client.post("/transfer", json={"from_id": "a", "to_id": "b", "amount": 50})
        client.post("/transfer", json={"from_id": "b", "to_id": "c", "amount": 75})
        client.post("/transfer", json={"from_id": "c", "to_id": "a", "amount": 25})
        
        # Calculate final total
        a = client.get("/account/a").json()["balance"]
        b = client.get("/account/b").json()["balance"]
        c = client.get("/account/c").json()["balance"]
        
        final_total = a + b + c
        assert final_total == initial_total

