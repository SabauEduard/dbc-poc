# Design-by-Contract Banking Demo 🏦

A demonstration of **Design-by-Contract (DbC)** principles applied in Python using modern tooling. This project showcases how contracts can strengthen testing, catch invalid states early, and integrate naturally with Python's test ecosystem.

## 📋 Overview

This demo implements a simple **Banking Service** with:

| Tool | Purpose |
|------|---------|
| **icontract** | DbC enforcement (preconditions, postconditions, invariants) |
| **pytest** | Unit tests and integration tests |
| **hypothesis** | Property-based testing |
| **FastAPI** | REST API with runtime contract validation |

The goal is to demonstrate how DbC **complements** testing rather than replaces it.

## 🗂️ Project Structure

```
dbc-poc/
├── app/
│   ├── __init__.py
│   ├── banking.py       # Business logic with DbC contracts
│   └── api.py           # FastAPI REST endpoints
├── tests/
│   ├── __init__.py
│   ├── test_banking_unit.py      # pytest unit tests
│   ├── test_banking_property.py  # hypothesis property tests
│   └── test_api_integration.py   # FastAPI integration tests
├── main.py              # Application entry point
├── requirements.txt
├── spec.md              # Original specification
└── README.md
```

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn app.api:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_banking_unit.py

# Run with coverage
pytest --cov=app
```

## 🏛️ Design-by-Contract Concepts

### Class Invariant

The `BankAccount` class maintains an invariant that the balance must never be negative:

```python
@icontract.invariant(lambda self: self.balance >= 0)
class BankAccount:
    ...
```

### Preconditions

Operations validate inputs before execution:

```python
@icontract.require(lambda amount: amount > 0, "Amount must be positive")
@icontract.require(lambda self, amount: self.balance >= amount, "Insufficient funds")
def withdraw(self, amount):
    ...
```

### Postconditions

Operations verify results after execution:

```python
@icontract.ensure(
    lambda OLD, self, amount: self.balance == OLD.balance + amount,
    "Balance must increase by deposit amount"
)
def deposit(self, amount):
    ...
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/deposit` | Deposit funds into an account |
| POST | `/withdraw` | Withdraw funds from an account |
| POST | `/transfer` | Transfer funds between accounts |
| GET | `/account/{id}` | Get account information |
| DELETE | `/accounts` | Clear all accounts (testing) |
| GET | `/health` | Health check |

### Example Requests

**Deposit:**
```bash
curl -X POST http://localhost:8000/deposit \
  -H "Content-Type: application/json" \
  -d '{"account_id": "alice", "amount": 100}'
```

**Withdraw:**
```bash
curl -X POST http://localhost:8000/withdraw \
  -H "Content-Type: application/json" \
  -d '{"account_id": "alice", "amount": 30}'
```

**Transfer:**
```bash
curl -X POST http://localhost:8000/transfer \
  -H "Content-Type: application/json" \
  -d '{"from_id": "alice", "to_id": "bob", "amount": 50}'
```

## 🧪 Testing Strategy

### Unit Tests (`test_banking_unit.py`)

Traditional pytest tests covering:
- ✅ Valid operations (deposits, withdrawals, transfers)
- ❌ Contract violations (negative amounts, insufficient funds)
- 🔄 Edge cases (exact balance withdrawal, tiny/large amounts)

### Property-Based Tests (`test_banking_property.py`)

Hypothesis-driven tests verifying:
- **Deposit property**: Balance increases by exactly the deposit amount
- **Withdraw property**: Balance decreases by exactly the withdrawal amount  
- **Transfer property**: Total system balance remains constant
- **Invariant**: Balance ≥ 0 after any valid operation sequence

Example property:
```python
@given(initial=initial_balances, amount=positive_amounts)
def test_deposit_increases_balance_by_amount(self, initial, amount):
    account = BankAccount("test", initial_balance=initial)
    old_balance = account.balance
    account.deposit(amount)
    assert account.balance == old_balance + amount
```

### Integration Tests (`test_api_integration.py`)

FastAPI TestClient tests verifying:
- HTTP status codes (200, 409, 422)
- Error response format consistency
- End-to-end banking workflows

## 🔴 Error Handling

Contract violations map to HTTP errors:

| Violation | HTTP Status | Error Code |
|-----------|-------------|------------|
| Invalid amount (≤ 0) | 422 | `invalid_amount` |
| Insufficient funds | 409 | `insufficient_funds` |
| Self-transfer | 422 | `invalid_transfer` |
| Other violations | 400 | `contract_violation` |

Example error response:
```json
{
  "detail": {
    "error": "insufficient_funds",
    "message": "Insufficient funds for withdrawal",
    "context": "withdraw"
  }
}
```

## 🎯 Demo Goals

This demonstration shows:

1. **Contracts catching programmer mistakes** - Invalid states are detected immediately
2. **Hypothesis discovering edge cases** - Property tests find bugs humans miss
3. **pytest integrating cleanly with DbC** - Contract violations become test failures
4. **FastAPI enforcing contracts** - HTTP clients receive meaningful errors
5. **DbC + Tests > Tests alone** - The combination provides stronger guarantees

## 📚 Key Learnings

### When to Use DbC

- **Invariants**: Properties that must always hold (e.g., balance ≥ 0)
- **Preconditions**: Input validation at function boundaries
- **Postconditions**: Verify complex state transitions

### DbC vs Assertions vs Tests

| Approach | Runtime | Documentation | Coverage |
|----------|---------|---------------|----------|
| DbC | Always checked | Self-documenting | All calls |
| Assertions | Debug only | Less formal | All calls |
| Tests | Test time | Separate files | Sampled |

## ⚠️ Non-Goals

This demo intentionally excludes:
- Authentication/authorization
- Persistent storage
- Concurrency handling
- Full banking domain complexity

## 📄 License

MIT License - See [LICENSE](LICENSE) file.
