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
| `JWT_SECRET_KEY` | Secret key for JWT tokens |
| `DATABASE_URL` | Database connection string |
| `FRONTEND_ORIGINS` | Allowed frontend CORS origins (comma-separated) |
| `ADMIN_PASSWORD` | Password for the default admin staff account |

## Run

```bash
python main.py