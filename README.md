# Study Mates

A real-time tutorial session management tool for university tutorials. Staff (tutors/lecturers) create sessions and students join with a 6-letter code. The system automatically assigns students into study groups based on GPA compatibility and schedule availability, then facilitates timed group discussions.

## Live Demo

| Service | URL |
|---|---|
| Frontend | https://study-mates-deployment.vercel.app |
| Backend | https://study-mates-deployment.onrender.com |

## Features

- **Staff**: Continue as a guest, or sign up for and sign in to an account, then create and manage tutorial sessions, configure group size, discussion time, and which student details are asked for, lock joining, remove students or move them between groups, trigger automatic group assignment, and control the timer
- **Custom Details**: Staff can ask students their own questions (single or multiple choice), which are display only, or used to group similar answers together, or mix different answers across groups
- **Accounts**: Staff with an account can save custom details and presets of their tutorial settings to reuse in later sessions
- **Students**: Join sessions anonymously via code, input GPA and availability, get assigned to a compatible group, introduce themselves, and participate in guided discussions
- **Match History and Connections**: Students see who they've met in each round, and (when turned on by the tutor) can connect with classmates they'd like to team up with. Students who connect with each other are told at the wrap-up, and each student's results are saved to their own device
- **Smart Grouping**: Groups are formed using a compatibility matrix scored on GPA similarity, goal alignment, and preferences, along with the times that the entire group is available — with rematch penalties to avoid repeated pairings across rounds, and swaps between groups to improve them all
- **Real-time Updates**: All session state (lobby, groups, discussion) is pushed live to all connected clients via WebSocket
- **Reconnection Handling**: Students and staff keep their place in a session across page refreshes and dropped connections (students stay in the session until they leave, are removed, or it ends). Sessions end automatically after being idle for an hour

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, React Router DOM v7, Socket.IO Client |
| Backend | Python, Flask, Flask-SocketIO (gevent) |
| Auth | JWT access tokens for staff (guest or account), anonymous UUID + localStorage (students) |
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

- Node.js 20.19+ (or 22.12+)
- Python 3.12+

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env # Then set the secret keys (see backend/README.md)
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
     [Lobby]     — students enter and wait
       ↓
    [Groups]     — staff triggers auto-grouping; students see their team
       ↓
 [Introductions] — a 30 second countdown for students to introduce themselves
       ↓
  [Discussion]   — starts automatically; groups receive 3 discussion questions
       ↓
    [Groups]     — the next round, with different group members
       ⋮
    [Wrap-Up]    — staff ends the tutorial; everyone returns to their seats (and
                   connections are revealed), until staff close the session
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FLASK_SECRET_KEY` | | Flask session secret |
| `JWT_SECRET_KEY` | | Staff access token secret — **the server won't start without it** (`FLASK_SECRET_KEY` is used if only it is set) |
| `JWT_EXPIRATION_HOURS` | `24` | Hours until a staff sign in expires |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///study_mates.sqlite` | Database connection string: SQLite (a local file), or a Postgres URL (`postgresql://...`) — **use Postgres when deployed**, as hosts like Render clear local files on every deploy and restart |
| `FRONTEND_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated CORS allowed origins — **must include the deployed frontend** |
| `VITE_BACKEND_URL` | `http://localhost:5000` (development only) | Backend URL used by the frontend |
| `PORT` | `5000` | Port the backend listens on |
| `DEBUG` | `False` | Enable Flask debug mode |
