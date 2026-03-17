# FastAPI Auth Module

A production-ready, modular authentication system built with **FastAPI**, **PostgreSQL**, **Redis**, and **ARQ** background workers. Designed with clean architecture, separation of concerns, and best software engineering practices.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Background Worker](#background-worker)
- [Security Considerations](#security-considerations)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.135+ |
| Language | Python 3.12+ |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Cache / Queue | Redis 7 |
| Background Jobs | ARQ (Async Redis Queue) |
| Password Hashing | passlib + bcrypt |
| JWT | python-jose |
| Email | aiosmtplib (Gmail SMTP) |
| Containerization | Docker + Docker Compose |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                               │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                       │
│                                                             │
│   Controller  →  Service  →  Repository  →  PostgreSQL      │
│       │              │                                      │
│       │              └──────────────────→  Redis (OTP)      │
│       │              └──────────────────→  ARQ Queue        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     ARQ Worker                              │
│   polls Redis Queue  →  sends email via Gmail SMTP          │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

```
HTTP Request
    ↓
Controller          validates schema, calls service
    ↓
Service             business logic, calls repository + Redis + ARQ
    ↓
Repository          executes DB queries via SQLAlchemy
    ↓
PostgreSQL

← on error anywhere →
core/exceptions.py  raised
core/handlers.py    caught, returns consistent JSON response
```

### Docker Services

```
┌──────────────────┐     ┌──────────────┐     ┌──────────────────┐
│   FastAPI App    │     │    Redis     │     │   ARQ Worker     │
│   port: 8000     │────▶│   port:6379  │◀────│   (no port)      │
└────────┬─────────┘     └──────────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│   PostgreSQL     │
│   port: 5432     │
└──────────────────┘
```

### Layer Responsibilities

| Layer | File | Responsibility |
|---|---|---|
| Controller | `auth/controller.py` | Receive HTTP request, call service, return response |
| Service | `auth/service.py` | Business logic, orchestrates repository + Redis + ARQ |
| Repository | `auth/repository.py` | All DB queries via SQLAlchemy, no business logic |
| Security | `core/security.py` | JWT, password hashing, OTP generation |
| Exceptions | `core/exceptions.py` | Custom exception classes |
| Handlers | `core/handlers.py` | Global exception → consistent JSON response |
| Worker | `app/worker/tasks.py` | Background email tasks via ARQ |

---

## Project Structure

```
project-root/
├── app/
│   ├── __init__.py
│   ├── main.py                        # App entry, router + handler registration
│   ├── core/
│   │   ├── config.py                  # pydantic-settings, env vars
│   │   ├── security.py                # JWT + password hashing + OTP
│   │   ├── dependencies.py            # get_current_user FastAPI dependency
│   │   ├── email.py                   # SMTP email utility
│   │   ├── exceptions.py              # All custom exception classes
│   │   └── handlers.py                # Global exception handlers
│   ├── db/
│   │   ├── base.py                    # SQLAlchemy Base + TimestampMixin
│   │   ├── session.py                 # Async engine + get_db dependency
│   │   └── redis.py                   # ARQ Redis pool + get_redis dependency
│   ├── modules/
│   │   └── auth/
│   │       ├── model.py               # User + RefreshToken ORM models
│   │       ├── schema.py              # Pydantic request/response schemas
│   │       ├── repository.py          # All DB queries (AuthRepository class)
│   │       ├── service.py             # Business logic (AuthService class)
│   │       └── controller.py          # Route handlers (FastAPI router)
│   ├── api/
│   │   └── v1/
│   │       └── router.py              # Aggregates all v1 routers
│   └── worker/
│       ├── tasks.py                   # ARQ task function definitions
│       └── settings.py                # ARQ WorkerSettings configuration
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── test_auth_service.py
│   └── integration/
│       └── test_auth_endpoints.py
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── run_worker.py                      # ARQ worker entry point
├── entrypoint.sh                      # Runs migrations then starts uvicorn
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Database Schema

### `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default: uuid4 | Unique user identifier |
| first_name | VARCHAR(50) | NOT NULL | User's first name |
| last_name | VARCHAR(50) | NOT NULL | User's last name |
| email | VARCHAR(255) | UNIQUE, INDEX, NOT NULL | User's email address |
| hashed_password | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| is_active | BOOLEAN | NOT NULL, default: True | Account active status |
| is_verified | BOOLEAN | NOT NULL, default: False | Email verification status |
| created_at | TIMESTAMPTZ | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Record last update timestamp |

### `refresh_tokens`

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, default: uuid4 | Unique token identifier |
| user_id | UUID | FK → users.id CASCADE, INDEX | Token owner |
| token_hash | VARCHAR(255) | NOT NULL, INDEX | SHA-256 hash of raw token |
| expires_at | TIMESTAMPTZ | NOT NULL | Token expiry timestamp |
| is_revoked | BOOLEAN | NOT NULL, default: False | Revocation status |
| created_at | TIMESTAMPTZ | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Record last update timestamp |

### Redis Keys

| Key Pattern | Value | TTL | Purpose |
|---|---|---|---|
| `email_verification:{user_id}` | 6-digit OTP | 10 mins | Email verification |
| `password_reset:{user_id}` | 6-digit OTP | 15 mins | Password reset |

---

## API Endpoints

Base URL: `/api/v1/auth`

All responses follow this consistent shape:

```json
{
  "status": "success | error",
  "message": "Human readable message",
  "data": { } 
}
```

---

### `POST /register`

Creates a new user account and sends a verification OTP to the provided email.

**Request Body**

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "password123",
  "confirm_password": "password123"
}
```

**Response `201`**

```json
{
  "status": "success",
  "message": "Registration successful. OTP sent to your email.",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "is_active": true,
    "is_verified": false
  }
}
```

**Error Responses**

| Status | Description |
|---|---|
| 409 | Email already registered |
| 422 | Validation failed (password mismatch, invalid email) |

---

### `POST /verify-email`

Verifies user's email using the OTP received after registration.

**Request Body**

```json
{
  "email": "john@example.com",
  "otp": "123456"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Email verified successfully.",
  "data": null
}
```

**Error Responses**

| Status | Description |
|---|---|
| 400 | Invalid OTP |
| 400 | OTP has expired |
| 400 | Email already verified |
| 404 | User not found |

---

### `POST /resend-verification-otp`

Resends a fresh OTP to the user's email for verification.

**Request Body**

```json
{
  "email": "john@example.com"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Verification OTP resent to your email.",
  "data": null
}
```

**Error Responses**

| Status | Description |
|---|---|
| 400 | Email already verified |
| 404 | User not found |

---

### `POST /login`

Authenticates a user and returns a JWT access token and refresh token.

**Request Body**

```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Login successful.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "a1b2c3d4e5f6...",
    "token_type": "bearer"
  }
}
```

**Error Responses**

| Status | Description |
|---|---|
| 401 | Invalid email or password |
| 403 | Account inactive |
| 403 | Email not verified |

---

### `POST /refresh-token`

Issues a new access token using a valid refresh token. Rotates the refresh token on every call.

**Request Body**

```json
{
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Token refreshed successfully.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new_token_here...",
    "token_type": "bearer"
  }
}
```

**Error Responses**

| Status | Description |
|---|---|
| 401 | Invalid token |
| 401 | Refresh token expired |
| 401 | Refresh token revoked |

---

### `POST /logout`

Revokes the user's refresh token. Requires a valid access token.

**Headers**

```
Authorization: Bearer <access_token>
```

**Request Body**

```json
{
  "refresh_token": "a1b2c3d4e5f6..."
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Logged out successfully.",
  "data": null
}
```

**Error Responses**

| Status | Description |
|---|---|
| 401 | Invalid or expired access token |
| 401 | Invalid refresh token |

---

### `POST /forgot-password`

Sends a password reset OTP to the user's email. Always returns `200` regardless of whether the email exists — prevents email enumeration.

**Request Body**

```json
{
  "email": "john@example.com"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "If that email exists, a reset OTP was sent.",
  "data": null
}
```

> Always returns `200` regardless of whether the email exists.

---

### `POST /reset-password`

Resets the user's password using the OTP received via email. Revokes all existing refresh tokens.

**Request Body**

```json
{
  "email": "john@example.com",
  "otp": "123456",
  "new_password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Password reset successfully.",
  "data": null
}
```

**Error Responses**

| Status | Description |
|---|---|
| 400 | Invalid OTP |
| 400 | OTP has expired |
| 404 | User not found |
| 422 | Validation failed (password mismatch) |

---

### `POST /change-password`

Changes the password for an authenticated user. Revokes all refresh tokens forcing re-login on all devices.

**Headers**

```
Authorization: Bearer <access_token>
```

**Request Body**

```json
{
  "current_password": "password123",
  "new_password": "newpassword123",
  "confirm_password": "newpassword123"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Password changed successfully.",
  "data": null
}
```

**Error Responses**

| Status | Description |
|---|---|
| 400 | Current password incorrect |
| 401 | Invalid or expired access token |
| 422 | Validation failed (password mismatch) |

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone The Repository

```bash
git clone https://github.com/ftanvir/fasatapi-auth.git
cd fastapi-auth
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your values — see [Environment Variables](#environment-variables).

### 3. Build And Start

```bash
docker compose up --build
```

This will:
- Start PostgreSQL
- Start Redis
- Run Alembic migrations automatically
- Start the FastAPI app on `http://localhost:8000`
- Start the ARQ background worker

### 4. Verify Everything Is Running

```bash
# app health
curl http://localhost:8000/docs

# check all services
docker compose ps

# app logs
docker compose logs -f app

# worker logs
docker compose logs -f worker
```

### 5. Stop The Project

```bash
# stop containers
docker compose down

# stop and remove volumes (fresh DB)
docker compose down -v
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values.

```bash
# App
APP_NAME="FastAPI Auth"
DEBUG=True

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_auth
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastapi_auth

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OTP
EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES=10
PASSWORD_RESET_OTP_EXPIRE_MINUTES=15

# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM=your@gmail.com
```

> **Gmail Setup:** Generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). Use this as `SMTP_PASSWORD`, not your Gmail login password.

---

## Background Worker

Email sending is handled asynchronously by an ARQ worker — keeping API response times fast regardless of SMTP latency.

### How It Works

```
POST /register
    ↓
create user + store OTP         (~15ms)
enqueue email task in Redis     (~2ms)
return response to client       ← fast

                                (independently)
ARQ worker picks up task
sends email via Gmail SMTP      (~1500ms)
retries on failure (3 attempts)
```

### Worker Configuration

| Setting | Value |
|---|---|
| Max retries | 3 |
| Retry delay | 5 seconds |
| Job timeout | 30 seconds |

### Monitoring Worker

```bash
docker compose logs -f worker
```

---

## Security Considerations

| Concern | Implementation |
|---|---|
| Password storage | bcrypt hashing via passlib |
| JWT signing | HS256 with secret key |
| Refresh token storage | SHA-256 hashed in Postgres, raw sent to client |
| Token rotation | Refresh token rotated on every `/refresh-token` call |
| Email enumeration | `/forgot-password` always returns 200 |
| Credential enumeration | `/login` returns same error for wrong email or password |
| OTP expiry | Auto-expiry via Redis TTL |
| Token revocation | All tokens revoked on password change/reset |
| UUID primary keys | Non-sequential, safe to expose in APIs |
| Input validation | Pydantic validators at schema boundary |

---

## API Documentation

Interactive API documentation is available at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)