# **spec.md — Main Demo: Design‑by‑Contract in Python**

## 📘 Overview
This demo showcases **Design‑by‑Contract (DbC)** applied in Python using modern tooling.  
It demonstrates how contracts can **strengthen testing**, catch invalid states early, and integrate naturally with Python’s test ecosystem.

The demo is centered around a tiny **Banking Service**, implemented with:
- **icontract** → DbC enforcement (preconditions, postconditions, invariants)  
- **pytest** → unit tests and integration tests  
- **hypothesis** → property‑based testing  
- **fastapi + fastapi‑icontract** → API with runtime contract validation  

The goal is to show how DbC complements testing, rather than replaces it.

---

# 1. **Scope**
This demo includes:

### ✔ Banking domain logic
- `BankAccount` class  
- Methods:  
  - `deposit(amount)`  
  - `withdraw(amount)`  
  - `transfer_to(other_account, amount)`  

### ✔ Contracts enforced with `icontract`
- **Preconditions** (e.g., amount > 0)  
- **Postconditions** (e.g., new balance calculated correctly)  
- **Class invariants** (e.g., balance ≥ 0)  
- **Old value snapshots** (using `snapshot=` or `OLD`)  

### ✔ Tests
- Unit tests (pytest)  
- Exception tests for contract violations  
- Property‑based tests (hypothesis) interacting with icontract  
- Integration tests for the API  

### ✔ REST API
- FastAPI routes wrapping the banking logic  
- DbC validation triggered for server‑side requests  
- Error responses mapped from contract violations  

---

# 2. **Project Structure**
project/
│
├── app/
│ ├── banking.py # main business logic + contracts
│ ├── api.py # fastapi app with fastapi-icontract
│ └── init.py
│
├── tests/
│ ├── test_banking_unit.py # pytest unit tests
│ ├── test_banking_property.py # hypothesis tests
│ ├── test_api_integration.py # FastAPI tests
│ └── init.py
│
├── main.py # optional: run FastAPI app
├── requirements.txt
└── spec.md # this file

---

# 3. **Business Logic Specification**

## 3.1 BankAccount Class

### **State**
| Field       | Type | Constraints |
|-------------|------|-------------|
| `balance`   | `int` or `float` | Must always be `>= 0` |

### **Invariants**
- `balance >= 0`

### **Operations**

#### **deposit(amount)**
| Type | Condition |
|------|-----------|
| Pre | `amount > 0` |
| Post | `balance == OLD.balance + amount` |

#### **withdraw(amount)**
| Type | Condition |
|------|-----------|
| Pre | `amount > 0` |
| Pre | `balance >= amount` |
| Post | `balance == OLD.balance - amount` |

#### **transfer_to(other, amount)**
| Type | Condition |
|------|-----------|
| Pre | `self != other` |
| Pre | `amount > 0` |
| Pre | `self.balance >= amount` |
| Post | `self.balance == OLD.self_balance - amount` |
| Post | `other.balance == OLD.other_balance + amount` |

All validations must be implemented with `@icontract.require`, `@icontract.ensure`, and `@icontract.invariant`.

---

# 4. **Testing Specification**

## 4.1 Unit Tests (pytest)
Each method must be tested for:
- Valid paths (normal usage)
- Invalid paths (contract violations)
- Edge cases  
  (e.g., withdrawing exactly the balance, depositing tiny or large amounts)

### Expected exceptions:
- `icontract._ViolationError` for any contract failure.

---

## 4.2 Property-Based Tests (hypothesis)

Property tests must verify:

### Deposit:
- For all positive `amount`, balance increases accordingly.

### Withdraw:
- For any valid amount ≤ balance, balance decreases accordingly.

### Transfer:
- Total system balance stays constant:  (old_self + old_other) == (new_self + new_other)

Hypothesis must also be configured to **try invalid values**, showing contract violations.

---

## 4.3 API Tests (FastAPI TestClient)
Test that:
- Valid requests succeed  
- Invalid requests trigger contract exceptions  
- Negative amounts return 422  
- Withdraw larger than balance returns 409 or similar  

API error format must be consistent.

---

# 5. **FastAPI Specification**

Endpoints:

### POST `/deposit`
```json
{ "account_id": "...", "amount": 100 }

POST /withdraw

{ "account_id": "...", "amount": 50 }

POST /transfer

{ "from_id": "...", "to_id": "...", "amount": 20 }

Requirements:

    Integrate with fastapi-icontract

    Map contract errors to HTTP errors

    Preserve invariant checks across API endpoints

6. Demo Goals (for Presentation)

Your live demonstration must show:
✔ Contracts catching programmer mistakes
✔ Hypothesis discovering edge cases automatically
✔ pytest integrating cleanly with DbC
✔ FastAPI enforcing contracts for HTTP clients
✔ Comparison:

    tests alone vs tests + DbC

7. Non‑Goals

This demo does not include:

    Authentication

    Persistent storage

    Concurrency handling

    Full banking domain logic

8. Requirements

icontract
pytest
hypothesis
fastapi
uvicorn
fastapi-icontract

