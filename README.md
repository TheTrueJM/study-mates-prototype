# Study Mates

A real-time tutorial session management tool for university tutorials. Staff (tutors/lecturers) create sessions and students join with a 6-letter code. The system automatically assigns students into study groups based on GPA compatibility and schedule availability, then facilitates timed group discussions.

## Live Demo

| Service | URL |
|---|---|
| Frontend | https://study-mates-deployment.vercel.app |
| Backend | https://study-mates-deployment.onrender.com |

## Features

- **Staff**: Continue as a guest or sign in to an account, then create and manage tutorial sessions, configure group size, discussion time, and which student details are asked for, trigger automatic group assignment, and control the discussion timer
- **Students**: Join sessions anonymously via code, input GPA and availability, get assigned to a compatible group, and participate in guided discussions
- **Smart Grouping**: Groups are formed using a compatibility matrix scored on GPA similarity, goal alignment, and schedule overlap — with rematch penalties to avoid repeated pairings across rounds
- **Real-time Updates**: All session state (lobby, groups, discussion) is pushed live to all connected clients via WebSocket
- **Reconnection Handling**: Students and staff keep their place in a session across page refreshes and dropped connections (students stay in the session until they leave or it ends)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, React Router DOM v7, Socket.IO Client |
| Backend | Python, Flask, Flask-SocketIO (eventlet) |
| Auth | JWT access tokens for staff (guest or account), anonymous UUID + sessionStorage (students) |
| Database | SQLite via Flask-SQLAlchemy (swappable via env var) |
| Grouping | NumPy (compatibility matrix calculation) |
| Deployment | Vercel (frontend), Render (backend) |

## Project Structure

```
study-mates-prototype/
├── frontend/       # React app — student and staff UI
└── backend/        # Flask server — REST API + WebSocket handlers
```

See [frontend/README.md](frontend/README.md) and [backend/README.md](backend/README.md) for setup instructions.

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The server starts on `http://localhost:5000`.

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app opens at `http://localhost:5173`.

## Session Flow

```
Staff creates tutorial → students join via 6-letter code
       ↓
    [Lobby]  — students enter and wait
       ↓
   [Groups]  — staff triggers auto-grouping; students see their team
       ↓
[Discussion] — staff starts timer; groups receive 3 discussion questions
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `insecure-key` | Flask session secret — **change in production** |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///study_mates.sqlite` | Database connection string |
| `FRONTEND_ORIGINS` | `http://localhost:5173` | Comma-separated CORS allowed origins |
| `VITE_BACKEND_URL` | `http://localhost:5000` | Backend URL used by the frontend |
| `PORT` | `5000` | Port the backend listens on |
| `DEBUG` | `False` | Enable Flask debug mode |
