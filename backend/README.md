# Study Mates - Backend

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

Copy the example environment file and fill in the required values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

| Variable | Description |
|---|---|
| `FLASK_SECRET_KEY` | Secret key for Flask sessions |
| `PORT` | Server port (default: 5000) |
| `DEBUG` | Enable Flask debug mode (default: false) |
| `SOCKETIO_LOGGER` | Log all Socket.IO events (default: false) |
| `JWT_SECRET_KEY` | Secret key for JWT tokens, which the server won't start without (`FLASK_SECRET_KEY` is used if only it is set) |
| `JWT_EXPIRATION_HOURS` | Hours until a staff sign in expires (default: 24) |
| `SQLALCHEMY_DATABASE_URI` | Database connection string (default: `sqlite:///study_mates.sqlite`) |
| `FRONTEND_ORIGINS` | Allowed frontend CORS origins (comma-separated, default: localhost only). Must include the deployed frontend's URL |

Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Run

```bash
python main.py
```

## Staff Accounts

Staff can use the application as a guest, or sign up for an account at `/staff/register` on the frontend. Both currently have the same access.

## Tests

```bash
python -m pytest
```
