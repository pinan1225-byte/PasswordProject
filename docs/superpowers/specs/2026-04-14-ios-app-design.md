# iOS Password Manager — Implementation Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a FastAPI REST backend to the existing project and build a SwiftUI iOS app that syncs with it over a local network (or via ngrok/frp for remote access).

**Architecture:** Server-side encryption — the iOS app sends the master password over HTTPS; the server encrypts/decrypts using the existing `CryptoManager`. The FastAPI layer is a thin adapter over the existing `UserManager` and `VaultManager` core. The iOS app is a separate Xcode project that communicates exclusively via the REST API.

**Tech Stack:** FastAPI, python-jose (JWT), uvicorn, Swift 5.9+, SwiftUI, URLSession

---

## Sub-project 1: FastAPI Backend

### File layout (inside existing repo)

```
src/password_manager/api/
├── __init__.py
├── main.py       # FastAPI app, CORS, router registration
├── auth.py       # /auth/register, /auth/login → JWT
├── vault.py      # /vault/entries CRUD
└── deps.py       # get_current_user, get_vault_manager dependency injection
```

New top-level entry point: `run_api.py` (project root) — starts uvicorn.

New dependencies to add to `pyproject.toml`:
- `fastapi>=0.110.0`
- `uvicorn[standard]>=0.29.0`
- `python-jose[cryptography]>=3.3.0`
- `passlib>=1.7.4`

### Auth flow

1. `POST /auth/register` — body: `{username, password}` → calls `UserManager.create_user`, returns `{user_id, username}`
2. `POST /auth/login` — body: `{username, password}` → calls `UserManager.authenticate_user`, on success returns `{access_token, token_type: "bearer"}`. Token payload: `{sub: user_id, exp: now+7days}`.
3. All `/vault/` routes require `Authorization: Bearer <token>` header. `deps.py` decodes the token and injects the authenticated `user_id`.

JWT secret key: read from env var `JWT_SECRET_KEY` (required, no default).

### Vault endpoints

All require authentication. `VaultManager` is constructed per-request in `deps.py` using the authenticated user's salt from `db.get_master_key(user_id)` and the master password from the request body where needed.

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET | `/vault/entries` | — (query: `search`, `category`, `tag`) | `[EntryOut]` (no plaintext password) |
| POST | `/vault/entries` | `EntryCreate` | `EntryOut` |
| GET | `/vault/entries/{id}` | — | `EntryOut` + `password` (decrypted) |
| PUT | `/vault/entries/{id}` | `EntryUpdate` | `EntryOut` |
| DELETE | `/vault/entries/{id}` | — | `{success: true}` |

`EntryCreate` body includes `master_password` field so the server can encrypt. `EntryUpdate` also includes `master_password`. `GET /vault/entries/{id}` requires `master_password` as a query param or request body.

### Pydantic schemas (in `api/vault.py`)

```python
class EntryCreate(BaseModel):
    master_password: str
    title: str
    username: str
    password: str
    url: str | None = None
    category: str | None = None
    notes: str | None = None
    tags: list[str] = []

class EntryUpdate(BaseModel):
    master_password: str
    title: str | None = None
    username: str | None = None
    password: str | None = None
    url: str | None = None
    category: str | None = None
    notes: str | None = None

class EntryOut(BaseModel):
    id: int
    title: str
    username: str
    url: str | None
    category: str | None
    notes: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    password: str | None = None  # only populated on GET /entries/{id}
```

### Error handling

- 401 Unauthorized: invalid/expired token, wrong master password (decrypt fails)
- 404 Not Found: entry not found or belongs to another user
- 422 Unprocessable Entity: Pydantic validation errors (FastAPI default)
- 500: unexpected server errors (logged, generic message returned)

---

## Sub-project 2: iOS SwiftUI App

New Xcode project: `PasswordManagerApp/` at the project root (not inside `src/`).

### File layout

```
PasswordManagerApp/
├── PasswordManagerApp.swift   # @main entry
├── Models/
│   ├── PasswordEntry.swift    # Codable, mirrors EntryOut
│   └── User.swift             # Codable login response
├── Services/
│   └── APIService.swift       # All URLSession calls, base URL configurable
├── Store/
│   └── AppStore.swift         # @Observable, holds entries + auth state
├── Views/
│   ├── LoginView.swift        # Login + Register tabs
│   ├── EntryListView.swift    # Grouped by category, search bar
│   ├── EntryDetailView.swift  # Show decrypted password, copy button
│   ├── AddEntryView.swift     # Form to add new entry
│   └── EditEntryView.swift    # Pre-filled form to edit entry
└── Utilities/
    └── KeychainHelper.swift   # Store JWT token + master password in Keychain
```

### State management

`AppStore` is an `@Observable` class injected via `.environment`. It holds:
- `token: String?` — JWT, persisted in Keychain
- `masterPassword: String?` — kept in memory only (never persisted to disk)
- `entries: [PasswordEntry]`
- `isLoggedIn: Bool`

On app launch: if Keychain has a token, show `EntryListView` and prompt for master password. If no token, show `LoginView`.

### APIService

Base URL stored in `UserDefaults` (configurable in a Settings screen). All requests attach `Authorization: Bearer <token>` header. Methods:

```swift
func login(username: String, password: String) async throws -> String  // returns token
func register(username: String, password: String) async throws
func listEntries(search: String?, category: String?) async throws -> [PasswordEntry]
func getEntry(id: Int, masterPassword: String) async throws -> PasswordEntry
func createEntry(_ entry: EntryCreate) async throws -> PasswordEntry
func updateEntry(id: Int, _ update: EntryUpdate) async throws -> PasswordEntry
func deleteEntry(id: Int) async throws
```

### Security

- JWT token stored in iOS Keychain (not UserDefaults)
- Master password held in memory only, cleared on logout
- HTTPS enforced in production; HTTP allowed for local dev (App Transport Security exception for `localhost` only)
- No plaintext passwords written to disk or logs

### Installation (no paid developer account needed)

1. Open `PasswordManagerApp/` in Xcode
2. Set your Apple ID as the signing team (free personal team)
3. Connect iPhone via USB, select it as target, press Run
4. On iPhone: Settings → General → VPN & Device Management → trust the developer certificate

Free personal provisioning profiles expire after 7 days and must be re-signed. For longer validity, an Apple Developer account ($99/year) is needed.

---

## Network access

For local WiFi: set base URL to `http://<mac-local-ip>:8000` (e.g. `http://192.168.1.5:8000`).

For remote access without a server: run `ngrok http 8000` on the Mac, use the ngrok HTTPS URL in the app. Free ngrok tier is sufficient for personal use.

---

## Out of scope

- Push notifications
- Face ID / Touch ID (can be added later as an enhancement)
- Password generator in the iOS app (can call a future `/vault/generate` endpoint)
- App Store distribution
