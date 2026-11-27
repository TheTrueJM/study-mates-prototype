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
| `SQLALCHEMY_DATABASE_URI` | Database connection string (default: `sqlite:///study_mates.sqlite`), or a Postgres URL (see [Database](#database)) |
| `FRONTEND_ORIGINS` | Allowed frontend CORS origins (comma-separated, default: localhost only). Must include the deployed frontend's URL |

Generate a secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Database

SQLite (a local `study_mates.sqlite` file) is used by default, which is all you need locally. Deployments should use **Postgres** instead, as hosts like Render clear local files on every deploy and restart (deleting staff accounts, saved details, and presets).

Set `SQLALCHEMY_DATABASE_URI` to a Postgres URL, e.g. `postgresql://user:password@host:5432/study_mates` (`postgres://` URLs work too). Tables are created automatically when the server starts.

To try Postgres locally (optional), e.g. with Docker:

```bash
docker run -d --name study-mates-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=study_mates -p 5432:5432 -v study-mates-db:/var/lib/postgresql/data postgres:17
# Then in .env:
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/study_mates
```

The tests use a temporary SQLite database, or `TEST_DATABASE_URI` to run against another database (which is **cleared**, so never point it at real data).

## Run

```bash
python main.py
```

## Staff Accounts

Staff can use the application as a guest, or sign up for an account at `/staff/register` on the frontend. Both can run tutorials, but only accounts can save custom details and settings presets.

| Route | Description |
|---|---|
| `POST /api/staff/register`, `POST /api/staff/login`, `POST /api/staff/guest` | Sign up, sign in, or continue as a guest (returns an access token) |
| `GET /api/staff/me` | The signed in staff member |
| `GET, POST /api/staff/attributes`, `PUT, DELETE /api/staff/attributes/<id>` | Custom details saved to the account |
| `GET, POST /api/staff/presets`, `PUT, DELETE /api/staff/presets/<id>` | Settings presets saved to the account (names are unique per account) |

New database tables are created on startup, and new discussion questions are added to existing databases.

## Tests

```bash
python -m pytest
```
