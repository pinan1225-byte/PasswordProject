# FastAPI Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a FastAPI REST API to the existing password manager so an iOS app can authenticate users and perform full CRUD on password entries.

**Architecture:** Thin FastAPI adapter layer over the existing `UserManager`, `VaultManager`, and `CryptoManager` core. JWT tokens identify users; master password is passed per-request for encrypt/decrypt operations. All business logic stays in the existing core — the API layer only handles HTTP concerns.

**Tech Stack:** FastAPI 0.110+, uvicorn, python-jose[cryptography], pytest, httpx (test client)

---

## File Structure

```
src/password_manager/api/
├── __init__.py          # empty
├── main.py              # FastAPI app, CORS, router registration, lifespan
├── deps.py              # get_db, get_current_user, get_vault_manager
├── auth.py              # /auth/register + /auth/login routers
├── vault.py             # /vault/entries CRUD routers
└── schemas.py           # Pydantic request/response models

run_api.py               # project root — uvicorn entry point
tests/api/
├── __init__.py
├── conftest.py          # FastAPI TestClient + SQLite in-memory DB fixture
├── test_auth.py
└── test_vault.py
```

**Modify:**
- `pyproject.toml` — add fastapi, uvicorn, python-jose, httpx dependencies

---

## Task 1: Add dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add API dependencies to pyproject.toml**

Replace the `dependencies` list with:

```toml
dependencies = [
    "cryptography>=42.0.0",
    "pycryptodome>=3.20.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "click>=8.1.0",
    "sqlalchemy>=2.0.0",
    "pymysql>=1.1.0",
    "argon2-cffi>=23.1.0",
    "python-dotenv>=1.0.0",
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "python-jose[cryptography]>=3.3.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 2: Install new dependencies**

```bash
.venv/bin/pip install fastapi "uvicorn[standard]" "python-jose[cryptography]" httpx
```

Expected: packages install without errors.

- [ ] **Step 3: Verify imports work**

```bash
.venv/bin/python -c "import fastapi, uvicorn, jose, httpx; print('OK')"
```

Expected: `OK`

---

## Task 2: Pydantic schemas

**Files:**
- Create: `src/password_manager/api/schemas.py`
- Create: `src/password_manager/api/__init__.py`

- [ ] **Step 1: Create empty `__init__.py`**

```python
# src/password_manager/api/__init__.py
```

- [ ] **Step 2: Write failing test for schema validation**

Create `tests/api/__init__.py` (empty) and `tests/api/test_schemas.py`:

```python
# tests/api/test_schemas.py
import pytest
from pydantic import ValidationError
from src.password_manager.api.schemas import (
    RegisterRequest, LoginRequest, EntryCreate, EntryUpdate, EntryOut, TokenResponse
)

def test_register_request_requires_username_and_password():
    with pytest.raises(ValidationError):
        RegisterRequest(username="", password="pass")

def test_entry_create_requires_master_password():
    with pytest.raises(ValidationError):
        EntryCreate(title="t", username="u", password="p")  # missing master_password

def test_entry_out_password_optional():
    from datetime import datetime
    e = EntryOut(
        id=1, title="t", username="u", url=None, category=None,
        notes=None, tags=[], created_at=datetime.now(), updated_at=datetime.now()
    )
    assert e.password is None
```

- [ ] **Step 3: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/api/test_schemas.py -v --override-ini="addopts="
```

Expected: `ImportError` — `schemas` module not found.

- [ ] **Step 4: Implement schemas.py**

```python
# src/password_manager/api/schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EntryCreate(BaseModel):
    master_password: str
    title: str = Field(..., min_length=1, max_length=255)
    username: str
    password: str
    url: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    tags: list[str] = []


class EntryUpdate(BaseModel):
    master_password: str
    title: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class EntryOut(BaseModel):
    id: int
    title: str
    username: str
    url: Optional[str]
    category: Optional[str]
    notes: Optional[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    password: Optional[str] = None  # only populated on GET /entries/{id}

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Run test to verify it passes**

```bash
.venv/bin/python -m pytest tests/api/test_schemas.py -v --override-ini="addopts="
```

Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add src/password_manager/api/ tests/api/ pyproject.toml
git commit -m "feat: add API schemas and dependencies"
```

---

## Task 3: JWT utilities in deps.py

**Files:**
- Create: `src/password_manager/api/deps.py`
- Test: `tests/api/test_deps.py`

- [ ] **Step 1: Write failing test**

```python
# tests/api/test_deps.py
import pytest
from src.password_manager.api.deps import create_access_token, decode_access_token

def test_token_roundtrip():
    token = create_access_token(user_id=42, secret="testsecret")
    user_id = decode_access_token(token, secret="testsecret")
    assert user_id == 42

def test_invalid_token_returns_none():
    result = decode_access_token("not.a.token", secret="testsecret")
    assert result is None

def test_expired_token_returns_none():
    from datetime import timedelta
    token = create_access_token(user_id=1, secret="s", expires_delta=timedelta(seconds=-1))
    result = decode_access_token(token, secret="s")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/python -m pytest tests/api/test_deps.py -v --override-ini="addopts="
```

Expected: `ImportError`

- [ ] **Step 3: Implement deps.py**

```python
# src/password_manager/api/deps.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.password_manager.config import get_settings
from src.password_manager.core import CryptoManager, VaultManager
from src.password_manager.storage import DatabaseManager

_bearer = HTTPBearer()

_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_DAYS = 7


def create_access_token(
    user_id: int,
    secret: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None else timedelta(days=_DEFAULT_EXPIRE_DAYS)
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


# --- FastAPI dependency functions ---

def get_db() -> DatabaseManager:
    db = DatabaseManager()
    db.initialize()
    return db


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> int:
    settings = get_settings()
    secret = settings.JWT_SECRET_KEY
    user_id = decode_access_token(credentials.credentials, secret)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user_id
```

- [ ] **Step 4: Add JWT_SECRET_KEY to Settings**

In `src/password_manager/config/settings.py`, add inside the `Settings` class after `MAX_LOGIN_ATTEMPTS`:

```python
JWT_SECRET_KEY: str = Field(
    default="change-this-secret-in-production",
    description="Secret key for JWT signing",
)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
.venv/bin/python -m pytest tests/api/test_deps.py -v --override-ini="addopts="
```

Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add src/password_manager/api/deps.py src/password_manager/config/settings.py tests/api/test_deps.py
git commit -m "feat: JWT token creation and validation"
```

---

## Task 4: Auth router

**Files:**
- Create: `src/password_manager/api/auth.py`
- Create: `tests/api/conftest.py`
- Create: `tests/api/test_auth.py`

- [ ] **Step 1: Create test conftest with TestClient**

```python
# tests/api/conftest.py
import pytest
from fastapi.testclient import TestClient

from src.password_manager.api.main import create_app
from src.password_manager.storage import DatabaseManager
from src.password_manager.storage.models import Base


@pytest.fixture
def db():
    manager = DatabaseManager(database_url="sqlite:///:memory:")
    manager.initialize()
    yield manager
    if manager._engine:
        Base.metadata.drop_all(manager._engine)
    manager.close()


@pytest.fixture
def client(db):
    app = create_app(db_override=db, jwt_secret="testsecret")
    return TestClient(app)
```

- [ ] **Step 2: Write failing auth tests**

```python
# tests/api/test_auth.py
def test_register_creates_user(client):
    resp = client.post("/auth/register", json={"username": "alice", "password": "pass123"})
    assert resp.status_code == 201
    assert resp.json()["username"] == "alice"

def test_register_duplicate_username_returns_409(client):
    client.post("/auth/register", json={"username": "bob", "password": "pass"})
    resp = client.post("/auth/register", json={"username": "bob", "password": "pass"})
    assert resp.status_code == 409

def test_login_returns_token(client):
    client.post("/auth/register", json={"username": "carol", "password": "mypass"})
    resp = client.post("/auth/login", json={"username": "carol", "password": "mypass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"username": "dave", "password": "correct"})
    resp = client.post("/auth/login", json={"username": "dave", "password": "wrong"})
    assert resp.status_code == 401
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/api/test_auth.py -v --override-ini="addopts="
```

Expected: `ImportError` — `main` module not found.

- [ ] **Step 4: Implement auth.py**

```python
# src/password_manager/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status

from src.password_manager.api.deps import create_access_token, get_db
from src.password_manager.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.password_manager.core import UserManager
from src.password_manager.storage import DatabaseManager

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: DatabaseManager = Depends(get_db)):
    user_manager = UserManager(db)
    try:
        user = user_manager.create_user(body.username, body.password, body.email)
    except Exception as exc:
        msg = str(exc)
        if "UNIQUE constraint" in msg or "Duplicate entry" in msg:
            raise HTTPException(status_code=409, detail="Username already exists")
        raise HTTPException(status_code=500, detail="Registration failed")
    return {"id": user.id, "username": user.username}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: DatabaseManager = Depends(get_db)):
    from src.password_manager.config import get_settings
    user_manager = UserManager(db)
    user = user_manager.authenticate_user(body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    secret = get_settings().JWT_SECRET_KEY
    token = create_access_token(user_id=user.id, secret=secret)
    return TokenResponse(access_token=token)
```

- [ ] **Step 5: Implement main.py**

```python
# src/password_manager/api/main.py
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.password_manager.api.auth import router as auth_router
from src.password_manager.api.vault import router as vault_router
from src.password_manager.storage import DatabaseManager


def create_app(
    db_override: Optional[DatabaseManager] = None,
    jwt_secret: Optional[str] = None,
) -> FastAPI:
    app = FastAPI(title="Password Manager API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if db_override is not None:
        from src.password_manager.api import deps
        deps._db_override = db_override

    if jwt_secret is not None:
        from src.password_manager.api import deps
        deps._jwt_secret_override = jwt_secret

    app.include_router(auth_router)
    app.include_router(vault_router)

    return app


app = create_app()
```

- [ ] **Step 6: Update deps.py to support test overrides**

Add at the top of `deps.py` after imports:

```python
_db_override: Optional[DatabaseManager] = None
_jwt_secret_override: Optional[str] = None


def get_db() -> DatabaseManager:
    if _db_override is not None:
        return _db_override
    db = DatabaseManager()
    db.initialize()
    return db


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> int:
    secret = _jwt_secret_override or get_settings().JWT_SECRET_KEY
    user_id = decode_access_token(credentials.credentials, secret)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user_id
```

Remove the old `get_db` and `get_current_user_id` definitions (they are replaced above).

- [ ] **Step 7: Create stub vault.py so main.py can import it**

```python
# src/password_manager/api/vault.py
from fastapi import APIRouter
router = APIRouter(prefix="/vault", tags=["vault"])
```

- [ ] **Step 8: Run auth tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/api/test_auth.py -v --override-ini="addopts="
```

Expected: `4 passed`

- [ ] **Step 9: Commit**

```bash
git add src/password_manager/api/ tests/api/
git commit -m "feat: auth register and login endpoints"
```

---

## Task 5: Vault router

**Files:**
- Modify: `src/password_manager/api/vault.py`
- Create: `tests/api/test_vault.py`

- [ ] **Step 1: Write failing vault tests**

```python
# tests/api/test_vault.py
import pytest


@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={"username": "user1", "password": "masterpass"})
    resp = client.post("/auth/login", json={"username": "user1", "password": "masterpass"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_entries_empty(client, auth_headers):
    resp = client.get("/vault/entries", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_entry(client, auth_headers):
    resp = client.post("/vault/entries", headers=auth_headers, json={
        "master_password": "masterpass",
        "title": "GitHub",
        "username": "alice",
        "password": "secret123",
        "category": "Work",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "GitHub"
    assert data["username"] == "alice"
    assert "password" not in data or data.get("password") is None


def test_get_entry_returns_decrypted_password(client, auth_headers):
    create_resp = client.post("/vault/entries", headers=auth_headers, json={
        "master_password": "masterpass",
        "title": "Gmail",
        "username": "bob",
        "password": "mypassword",
    })
    entry_id = create_resp.json()["id"]

    resp = client.get(
        f"/vault/entries/{entry_id}",
        headers=auth_headers,
        params={"master_password": "masterpass"},
    )
    assert resp.status_code == 200
    assert resp.json()["password"] == "mypassword"


def test_update_entry(client, auth_headers):
    create_resp = client.post("/vault/entries", headers=auth_headers, json={
        "master_password": "masterpass",
        "title": "Old Title",
        "username": "user",
        "password": "oldpass",
    })
    entry_id = create_resp.json()["id"]

    resp = client.put(f"/vault/entries/{entry_id}", headers=auth_headers, json={
        "master_password": "masterpass",
        "title": "New Title",
        "password": "newpass",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


def test_delete_entry(client, auth_headers):
    create_resp = client.post("/vault/entries", headers=auth_headers, json={
        "master_password": "masterpass",
        "title": "ToDelete",
        "username": "u",
        "password": "p",
    })
    entry_id = create_resp.json()["id"]

    resp = client.delete(f"/vault/entries/{entry_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    get_resp = client.get(
        f"/vault/entries/{entry_id}",
        headers=auth_headers,
        params={"master_password": "masterpass"},
    )
    assert get_resp.status_code == 404


def test_unauthenticated_request_returns_403(client):
    resp = client.get("/vault/entries")
    assert resp.status_code in (401, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/api/test_vault.py -v --override-ini="addopts="
```

Expected: most tests fail — vault router is a stub.

- [ ] **Step 3: Implement vault.py**

```python
# src/password_manager/api/vault.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.password_manager.api.deps import get_current_user_id, get_db
from src.password_manager.api.schemas import EntryCreate, EntryOut, EntryUpdate
from src.password_manager.core import CryptoManager, VaultManager
from src.password_manager.storage import DatabaseManager

router = APIRouter(prefix="/vault", tags=["vault"])


def _build_vault(user_id: int, master_password: str, db: DatabaseManager) -> VaultManager:
    master_key_data = db.get_master_key(user_id=user_id)
    if master_key_data:
        _, salt_hex = master_key_data
        salt = bytes.fromhex(salt_hex) if salt_hex else None
    else:
        salt = None

    crypto = CryptoManager(master_password, salt=salt)

    if not master_key_data:
        hashed, _ = CryptoManager.hash_password(master_password)
        db.save_master_key(hashed, crypto.salt.hex(), user_id=user_id)

    return VaultManager(crypto, db, user_id=user_id)


def _entry_to_out(entry, password: Optional[str] = None) -> EntryOut:
    return EntryOut(
        id=entry.id,
        title=entry.title,
        username=entry.username,
        url=entry.url,
        category=entry.category,
        notes=entry.notes,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        password=password,
    )


@router.get("/entries", response_model=list[EntryOut])
def list_entries(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: DatabaseManager = Depends(get_db),
):
    entries = db.list_entries(user_id=user_id, search=search, category=category, tag=tag)
    return [_entry_to_out(e) for e in entries]


@router.post("/entries", response_model=EntryOut, status_code=201)
def create_entry(
    body: EntryCreate,
    user_id: int = Depends(get_current_user_id),
    db: DatabaseManager = Depends(get_db),
):
    vault = _build_vault(user_id, body.master_password, db)
    entry = vault.add_entry(
        title=body.title,
        username=body.username,
        password=body.password,
        url=body.url,
        category=body.category,
        notes=body.notes,
        tags=body.tags,
    )
    vault._crypto.clear_key()
    return _entry_to_out(entry)


@router.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(
    entry_id: int,
    master_password: str = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: DatabaseManager = Depends(get_db),
):
    vault = _build_vault(user_id, master_password, db)
    entry = vault.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    try:
        decrypted = vault.get_decrypted_password(entry_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Wrong master password")
    vault._crypto.clear_key()
    return _entry_to_out(entry, password=decrypted)


@router.put("/entries/{entry_id}", response_model=EntryOut)
def update_entry(
    entry_id: int,
    body: EntryUpdate,
    user_id: int = Depends(get_current_user_id),
    db: DatabaseManager = Depends(get_db),
):
    vault = _build_vault(user_id, body.master_password, db)
    updated = vault.update_entry(
        entry_id=entry_id,
        title=body.title,
        username=body.username,
        password=body.password,
        url=body.url,
        category=body.category,
        notes=body.notes,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    vault._crypto.clear_key()
    return _entry_to_out(updated)


@router.delete("/entries/{entry_id}")
def delete_entry(
    entry_id: int,
    user_id: int = Depends(get_current_user_id),
    db: DatabaseManager = Depends(get_db),
):
    db_result = db.delete_entry(entry_id, user_id=user_id)
    if not db_result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}
```

- [ ] **Step 4: Run vault tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/api/test_vault.py -v --override-ini="addopts="
```

Expected: `7 passed`

- [ ] **Step 5: Run all API tests**

```bash
.venv/bin/python -m pytest tests/api/ -v --override-ini="addopts="
```

Expected: `11 passed` (4 auth + 7 vault)

- [ ] **Step 6: Commit**

```bash
git add src/password_manager/api/vault.py tests/api/test_vault.py
git commit -m "feat: vault CRUD endpoints"
```

---

## Task 6: Uvicorn entry point

**Files:**
- Create: `run_api.py`

- [ ] **Step 1: Create run_api.py**

```python
# run_api.py
"""Start the FastAPI server. Run: python run_api.py"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.password_manager.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

- [ ] **Step 2: Verify server starts**

```bash
.venv/bin/python run_api.py &
sleep 2
curl -s http://localhost:8000/docs | grep -q "Password Manager" && echo "Server OK"
kill %1
```

Expected: `Server OK`

- [ ] **Step 3: Commit**

```bash
git add run_api.py
git commit -m "feat: uvicorn entry point for API server"
```

---

## Task 7: Run full test suite

- [ ] **Step 1: Run all tests**

```bash
.venv/bin/python -m pytest tests/unit/ tests/integration/ tests/api/ \
  --ignore=tests/unit/test_init.py --override-ini="addopts=" -q
```

Expected: all tests pass, no errors.

- [ ] **Step 2: Manual smoke test**

```bash
# Terminal 1 — start server
JWT_SECRET_KEY=mysecret .venv/bin/python run_api.py

# Terminal 2 — register + login + create entry
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' | python3 -m json.tool

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/vault/entries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"master_password":"testpass","title":"GitHub","username":"alice","password":"secret123"}' \
  | python3 -m json.tool
```

Expected: entry created with an `id`, no `password` field in response.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: FastAPI backend complete — auth + vault CRUD"
```

---

## Self-Review

**Spec coverage:**
- ✅ POST /auth/register
- ✅ POST /auth/login → JWT
- ✅ GET /vault/entries (search, category, tag filters)
- ✅ POST /vault/entries
- ✅ GET /vault/entries/{id} (decrypted password)
- ✅ PUT /vault/entries/{id}
- ✅ DELETE /vault/entries/{id}
- ✅ JWT Bearer auth on all /vault/ routes
- ✅ JWT_SECRET_KEY from env/settings
- ✅ Reuses existing UserManager, VaultManager, CryptoManager

**Placeholder scan:** None found.

**Type consistency:** `EntryOut`, `EntryCreate`, `EntryUpdate` used consistently across schemas, vault router, and tests.
