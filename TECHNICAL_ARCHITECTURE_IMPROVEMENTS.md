# Study Mates — Technical Architecture Document (v2 Redesign)

## Document Purpose

This document outlines the complete technical redesign of the "Study Mates" application. It is intended to be given to an implementation AI that will create the entire v2 codebase from scratch under `backend-v2/` and `frontend-v2/` folders, using the original codebase (`backend/` and `frontend/`) only for context on the application's domain logic and overall purpose.

---

## 1. Application Overview

### 1.1 What is Study Mates?

Study Mates is a web application for university students to form effective assessment groups. Students input anonymized characteristics (GPA, goal grade, availability) and the system matches them into groups using a graph-based algorithm. Staff coordinate tutorial sessions and manage group formation/discussion rounds.

### 1.2 Key Principles

- **Student anonymity:** No PII collected (no names, emails, student numbers)
- **Minimal data collection:** Only session-relevant data, cleared after tutorial
- **In-memory only:** No persistent student data in any database
- **Cross-browser compatibility:** Must work on Safari, Chrome, Firefox, Edge across desktop and mobile
- **CORS-safe:** Frontend and backend will be hosted on different domains (e.g., Vercel + Render)
- **Staff accountability:** Staff have proper authentication (JWT) as registered users

---

## 2. Problem Statement (Why This Redesign Exists)

### 2.1 Current Issues (v1)

The original v1 codebase has critical CORS/cookie compatibility issues:

**Problem 1: Third-party cookies blocked by Safari**
- Backend (`backend/app/sockets/student.py` line 31) uses `request.cookies.get("tutorial_code")` to identify users
- Frontend (`frontend/src/pages/student/JoinTutorial.jsx` line 53) sends `credentials: "include"`
- When frontend and backend are on different domains, Safari blocks third-party cookies entirely
- Result: Tutorial code is never read, UUID identification fails, students lose their session on reconnect

**Problem 2: Client-managed UUID**
- UUID is generated client-side and stored in `localStorage`
- On reconnect, the UUID may be lost or mismatched
- No server-side validation of UUID existence

**Problem 3: REST API dependency for student auth**
- Student authentication relies on fetch API calls with cookies
- This is fundamentally incompatible with cross-origin hosting

### 2.2 Solution Summary

1. **Eliminate cookies for student auth entirely** — use Socket.IO auth parameter
2. **Server-manages all UUIDs** — no client-side UUID generation
3. **Use Flask signed sessions for staff** — or JWT for cross-instance compatibility
4. **All student identification via Socket.IO events** — no REST API for students
5. **In-memory session storage** — no database persistence for student data

---

## 3. New Authentication Architecture

### 3.1 Student Authentication (Socket.IO Only)

**No accounts, no passwords, no cookies, no JWT.**

#### 3.1.1 Connection Flow

```
1. Client connects to backend via Socket.IO
   - No auth parameter needed on initial connect
   - Socket.IO connects via WebSocket (or polling fallback)

2. Client emits "authenticate_student" event
   - Payload: { tutorial_code: "ABCDEF" }

3. Server validates tutorial_code
   - If tutorial exists and is active:
     - Generate UUID: uuid4()
     - Generate name: "Colour-Animal" format (e.g., "Blue-Elephant")
     - Create student record in tutorials[tutorial_code].students[uuid]
     - Store in session: session["uuid"] = uuid
     - Emit "authenticated" with { uuid, name, tutorial_code }
     - Join socket room: tutorial_<tutorial_code>

   - If tutorial doesn't exist or is ended:
     - Emit "authentication_failed" with { reason: "Tutorial not found or has ended" }
```

#### 3.1.2 Reconnection Handling

```
1. Client reconnects via Socket.IO (reconnection: true configured)

2. On "connect" event, client emits "reauthenticate_student"
   - Payload: { session_id: <from previous auth> }
   - OR server can detect reconnection via session cookie

3. Server looks up session["uuid"]
   - If found and tutorial still active:
     - Restore student to same room
     - Emit "reauthenticated" with { uuid, name, tutorial_code }
     - Student retains all previous data

   - If session expired or tutorial ended:
     - Emit "reauthentication_failed" with { reason: "Session expired or tutorial ended" }
     - Client must start from step 1
```

**Key Implementation Note:** Flask's `session` uses signed cookies. These are **first-party signed cookies** — Safari accepts them because they are cryptographically signed by the server and cannot be read/modified by other domains. This is different from regular third-party cookies.

#### 3.1.3 UUID Generation (Server-Side)

```python
import uuid

def generate_student_uuid():
    return str(uuid.uuid4())
```

**Never generate UUID on the client.** The server is the sole authority for UUID creation.

#### 3.1.4 Name Generation (Server-Side)

```python
import random

COLORS = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink", "Cyan", "Magenta", "Lime",
          "Indigo", "Violet", "Coral", "Teal", "Gold", "Silver", "Bronze", "Maroon", "Navy", "Azure"]
ANIMALS = ["Elephant", "Tiger", "Lion", "Bear", "Wolf", "Fox", "Eagle", "Hawk", "Dolphin", "Whale",
           "Panda", "Koala", "Kangaroo", "Penguin", "Owl", "Raven", "Falcon", "Shark", "Otter", "Deer"]

def generate_student_name():
    return f"{random.choice(COLORS)}-{random.choice(ANIMALS)}"
```

### 3.2 Staff Authentication (JWT)

**Staff are registered users with persistent accounts.** JWT is used for cross-instance compatibility and no server-side session storage requirement.

#### 3.2.1 Staff Account Storage

Staff accounts ARE stored in the SQLite database (unlike student data):

```python
# In backend/app/database/models.py (NEW)
class Staff():
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
```

#### 3.2.2 JWT Structure

```python
# JWT payload
{
    "user_id": <staff_db_id>,
    "username": "staff_username",
    "role": "staff",
    "iat": <issued_at_timestamp>,
    "exp": <expiration_timestamp>
}
```

- **Expiration:** 24 hours (configurable)
- **Signing algorithm:** HS256
- **Secret:** Stored in environment variable `JWT_SECRET_KEY`

#### 3.2.3 Staff Login Flow

```
1. Staff submits credentials via REST API
   POST /api/staff/login
   Body: { username: "staff_name", password: "password" }

2. Server verifies password (bcrypt)
   - If valid:
     - Generate JWT
     - Update last_login timestamp
     - Return { token: "<jwt>", username: "staff_name" }

   - If invalid:
     - Return 401 { error: "Invalid credentials" }
```

#### 3.2.4 Staff Socket.IO Authentication

```
1. Staff connects to Socket.IO
   - Client includes JWT in auth parameter:
     io(url, { auth: { token: "<jwt>" } })

2. Server verifies JWT on connect
   - If valid:
     - Extract user_id and username
     - Set session["staff_id"] = user_id
     - Join room: staff_<tutorial_code> (if applicable)
     - Emit "staff_authenticated" with { user_id, username }

   - If invalid/expired:
     - Disconnect or emit "authentication_failed"
```

#### 3.2.5 JWT Secret Configuration

```python
# In backend-v2/app/__init__.py or .env
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-in-production")
JWT_EXPIRATION_HOURS = 24
```

---

## 4. In-Memory Session Data Structure

### 4.1 Core Data Model

All tutorial data is stored in a single in-memory dictionary. **No database persistence for student data.**

```python
# Global in-memory store (in backend-v2/app/sockets/__init__.py)
tutorials = {}

# Structure:
tutorials = {
    "tutorial_code": {  # e.g., "ABCDEF"
        "staff_uuid": <staff_socket_uuid>,   # Staff's socket session UUID
        "name": "CS26 Tutorial 1",       # Tutorial name
        "state": "lobby",                    # See §4.2
        "group_size": 4,                     # Members per group
        "available_attributes": [            # Staff-selected attributes
            "currentGPA",
            "goalGPA",
            "availability"
        ],
        "students": {                        # UUID -> student record
            "<uuid>": {
                "name": "Blue-Elephant",
                "currentGPA": 4.5,           # null if not entered
                "goalGPA": 4.0,              # null if not entered
                "availability": {             # {DAY_CODE: TIME_PERIOD}
                    "MON": ["M", "E"],
                    "WED": ["M"]
                },
                "shared_attributes": [       # Student-toggled share list
                    "currentGPA",
                    "goalGPA"
                ],
                "group": None,               # Group ID or None
                "details_complete": False     # True if student submitted all entered data
            }
        },
        "groups": {                            # Group ID -> list of UUIDs
            "G1": ["uuid1", "uuid2", "uuid3", "uuid4"],
            "G2": ["uuid5", "uuid6", "uuid7", "uuid8"]
        },
        "questions": {                         # Pre-loaded discussion questions
            "What study techniques work best for you?" # "academic" category
            "How do you like to unwind after a long day?" # "casual" category
            "When did you realise you wanted to study your course?" # "smart" category
        },
        "timer": {                             # Current timer state
            "duration": 0,                     # Seconds
            "remaining": 0,                    # Seconds
            "running": False,
        },
        "discussion_duration": 600,            # 10 minutes (configurable by staff)
        "last_activity": 1690000000,           # Unix timestamp
    }
}
```

### 4.2 Tutorial States

```python
VALID_STATES = ["lobby", "groups", "discussion"]

# State transitions:
lobby → groups        (staff initiates round)
groups → discussion   (staff starts discussion)
discussion → groups   (discussion timer ends, groups re-displayed)
groups → lobby        (staff returns to lobby)
any → ended           (staff ends tutorial or auto-expires)
```

**State rules:**
- **lobby:** Students can join and enter details. No groups formed.
- **groups:** Groups are formed and displayed. Students are seating. No timer running.
- **discussion:** Discussion timer running. Groups displayed with questions.
- **ended:** All data cleared. Students kicked. No further actions.

### 4.3 Available Attributes (Staff-Toggled)

When staff creates a tutorial, they select which attributes students can enter:

```python
ALL_ATTRIBUTES = ["currentGPA", "goalGPA", "availability"]

# Default: all attributes available
# Staff can deselect any:
available_attributes = ["currentGPA", "goalGPA"]  # availability disabled
```

### 4.4 Student Share Toggles (Student-Toggled)

Each student can individually choose which attributes to share with others:

```python
# Default: all attributes hidden (not shared)
shared_attributes = []  # empty = nothing shared

# Student enables sharing per-attribute:
shared_attributes = ["currentGPA"]  # only GPA shared, goalGPA and availability hidden
```

**Important:** When displaying student info to other students, only show attributes in `shared_attributes`. Hidden attributes show as "Hidden" or "Not shared".

---

## 5. Updated Tutorial Workflow

### 5.1 Complete Workflow Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: TUTORIAL SETUP (Staff)                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. Staff accesses tutorial setup page                           │
│ 2. Staff enters:                                                │
│    - Tutorial name                                              │
│    - Group size                                                 │
│    - Discussion duration (default: 600s / 10min)                │
│    - Available attributes (toggles for each)                    │
│ 3. Staff clicks "Create Tutorial"                               │
│ 4. Server:                                                      │
│    - Generates unique tutorial code (6 random uppercase chars)  │
│    - Creates tutorial in memory with staff_id                   │
│    - Initializes all default values                             │
│ 5. Server returns tutorial code to staff                        │
│ 6. Staff view shows lobby with code, QR, and student list       │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: STUDENT JOINING                                        │
├─────────────────────────────────────────────────────────────────┤
│ 1. Student opens app, sees "Enter Tutorial Code" screen         │
│ 2. Student enters tutorial code (e.g., "ABCDEF")                │
│ 3. Student clicks "Join"                                        │
│ 4. Client emits socket event: "join_tutorial" { code: "ABCDEF" }│
│ 5. Server validates code, generates UUID & name, creates record │
│ 6. Server emits "authenticated" to student                      │
│ 7. Student enters details page (only if tutorial is in lobby)   │
│ 8. Student submits details → Server updates student record      │
│ 9. Student enters lobby → Server emits "tutorial_state"         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: GROUP FORMATION & DISCUSSION (Automated)               │
├─────────────────────────────────────────────────────────────────┤
│ 1. Staff clicks "Form Groups" (from lobby)                      │
│ 2. Server:                                                      │
│    - Runs matching algorithm (see §7)                           │
│    - Sets state to "groups"                                     │
│    - Emits "groups_formed" with group assignments               │
│ 3. Staff clicks "Start Discussion"                              │
│ 4. Server:                                                      │
│    - Sets state to "discussion"                                 │
│    - Emits "discussion_started" discussion durations            │
│ 6. Discussion timer elapses (auto)                              │
│ 8. Staff chooses: "next groups" or "back to lobby"              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: ENDING                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. Staff clicks "End Tutorial"                                  │
│ 2. Server:                                                      │
│    - Sets state to "ended"                                      │
│    - Clears all student data                                    │
│    - Emits "tutorial_ended" to all clients                      │
│ 3. Clients redirect to home page                                │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 State Transition Diagram

```
                    staff "start round"
                         │
                    ┌────┴────┐
                    │ groups  │
                    └────┬────┘
                         │
                    staff "start discussion"
                         │
                    ┌────┴────┐
                    │discussion│
                    └────┬────┘
                         │
                    timer ends (auto)
                         │
                    ┌────┴────┐
                    │ groups  │
                    └────┬────┘
                         │
              ┌──────────┴──────────┐
              │                     │
        staff "next round"    staff "lobby"
              │                     │
         ┌────┴────┐           ┌────┴────┐
         │ groups  │           │  lobby  │
         └────┬────┘           └────┬────┘
              │                     │
              └──────────┬──────────┘
                         │
                    staff "end tutorial"
                         │
                    ┌────┴────┐
                    │  ended  │
                    └─────────┘
```

### 5.3 Key Differences from v1

| Aspect | v1 | v2 | |--------|----|----| | Student auth | Cookie + client UUID | Socket.IO event + server UUID | | Student data storage | Database | In-memory only | | UUID generation | Client-side | Server-side | | Tutorial code lookup | Cookie | Socket event | | Reconnection | Cookie-based | Session-based | | Staff auth | Flask session | JWT | | Timer management | Manual staff control | Auto intro → auto discussion | | Share toggles | Not implemented | Student-toggled per attribute | | Available attributes | All always available | Staff-toggled per tutorial |

## 6. Socket.IO Event Specification

### 6.1 All Events

#### 6.1.1 Student Events

Client → Server Events:

| Event | Payload | Description | |-------|---------|-------------| | join_tutorial | { code: string } | Student joins tutorial by code | | update_details | { currentGPA?: float, goalGPA?: float, availability?: {DAY: [periods]}, sharedAttributes?: string[] } | Student updates their attributes | | enter_tutorial | {} | Student confirms details and enters lobby | | rejoin_tutorial | {} | Student reconnects and re-enters (after tutorial_ended) |

Server → Client Events:

| Event | Payload | Description | |-------|---------|-------------| | authenticated | { uuid: string, name: string, tutorial_code: string } | Student successfully authenticated | | join_failed | { reason: string } | Tutorial not found or ended | | tutorial_state | { state: string, students: [...], groups: {...}, timer: {...}, round: int } | Current tutorial state | | students_updated | { students: [...] } | Student list changed | | groups_formed | { groups: {G1: [uuid, ...], ...}, round: int } | Groups formed for current round | | discussion_started | { intro_duration: 30, discussion_duration: int, questions: [...] } | Discussion phase begins | | timer_update | { remaining: int, phase: "intro" \| "discussion" } | Timer tick (every second) | | timer_expired | { phase: "intro" \| "discussion" } | Timer ended | | tutorial_ended | {} | Tutorial is over, redirect to home | | error | { message: string } | Error notification |

#### 6.1.2 Staff Events

Client → Server Events:

| Event | Payload | Description | |-------|---------|-------------| | create_tutorial | { name: string, group_size: int, discussion_duration: int, available_attributes: string[] } | Create new tutorial | | start_round | {} | Start group formation round | | start_discussion | {} | Start discussion (intro + auto discussion) | | next_round | {} | Start next round from groups state | | back_to_lobby | {} | Return to lobby from groups state | | end_tutorial | {} | End tutorial | | update_tutorial | { name?: string, group_size?: int, discussion_duration?: int, available_attributes?: string[] } | Update tutorial settings |

Server → Client Events:

| Event | Payload | Description | |-------|---------|-------------| | tutorial_created | { code: string, name: string } | Tutorial created, code returned | | round_started | { groups: {G1: [uuid, ...], ...}, round: int } | Groups formed | | discussion_started | { intro_duration: 30, discussion_duration: int, questions: [...] } | Discussion begins | | timer_update | { remaining: int, phase: "intro" \| "discussion" } | Timer tick | | timer_expired | { phase: "intro" \| "discussion" } | Timer ended | | tutorial_ended | {} | Tutorial over | | students_updated | { students: [...] } | Student list changed | | error | { message: string } | Error notification |

### 6.2 Room Structure

```
tutorial_<code>      - All students in tutorial
staff_<code>         - Staff member for tutorial
staff_global         - Staff can see all active tutorials
```

### 6.3 Socket.IO Configuration

```
// Backend (Flask-SocketIO)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading", 
                    ping_timeout=60, ping_interval=25, max_http_buffer_size=1e7)

// Frontend (Socket.IO client)
const socket = io(backend_url, {
    transports: ["websocket", "polling"],  // fallback to polling
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 10,
    timeout: 20000
});
```

## 7. Group Matching Algorithm

### 7.1 Algorithm Overview

The algorithm uses a graph-based approach where nodes are students and weighted edges represent shared characteristics.

### 7.2 Edge Weight Calculation

For each pair of students A and B:

```
def calculate_edge_weight(student_a, student_b):
    weight = 0
    
    # GPA similarity (max weight: 5)
    if student_a.currentGPA and student_b.currentGPA:
        diff = abs(student_a.currentGPA - student_b.currentGPA)
        gpa_weight = max(0, 5 - (diff * 5))  # 5 if same, 0 if diff >= 1.0
        weight += gpa_weight
    
    # Goal GPA similarity (max weight: 5)
    if student_a.goalGPA and student_b.goalGPA:
        diff = abs(student_a.goalGPA - student_b.goalGPA)
        goal_weight = max(0, 5 - (diff * 5))
        weight += goal_weight
    
    # Availability overlap (max weight: 1 per shared slot)
    if student_a.availability and student_b.availability:
        shared_slots = student_a.availability.intersection(student_b.availability)
        weight += len(shared_slots)
    
    return weight
```

### 7.3 Normalization

Normalize weights to 0-1 range

``` 
max_weight = max(all_edge_weights)
for edge in edges:
    edge.normalized_weight = edge.weight / max_weight if max_weight > 0 else 0
```

### 7.4 Group Formation Algorithm

```
def form_groups(tutorial_code, group_size, previous_matches=None):
    tutorial = tutorials[tutorial_code]
    students = list(tutorial.students.values())
    
    if len(students) < group_size:
        return { "error": "Not enough students for group size" }
    
    # Build adjacency dictionary
    adjacency = {}  # uuid -> {other_uuid: normalized_weight}
    for i, student_i in enumerate(students):
        adjacency[student_i["uuid"]] = {}
        for j, student_j in enumerate(students):
            if i != j:
                weight = calculate_edge_weight(student_i, student_j)
                normalized = weight / max_weight if max_weight > 0 else 0
                adjacency[student_i["uuid"]][student_j["uuid"]] = normalized
    
    # Algorithm state
    unmatched = set(s["uuid"] for s in students)
    groups = {}  # group_id -> [uuids]
    previous_matches = previous_matches or {}  # uuid -> set of matched uuids
    threshold = max(0.45, 0.75 - (tutorial.round * 0.1))  # decreases each round
    
    while unmatched:
        current_uuid = random.choice(list(unmatched))
        current_group = [current_uuid]
        unmatched.remove(current_uuid)
        queue = deque()
        
        # Get neighbors sorted by weight (descending)
        neighbors = sorted(
            adjacency[current_uuid].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for neighbor_uuid, weight in neighbors:
            if neighbor_uuid not in unmatched:
                continue
            
            # Check previous matches
            prev_matches = previous_matches.get(current_uuid, set())
            if neighbor_uuid in prev_matches:
                # Re-match only with random chance (35%)
                if random.random() > 0.35:
                    continue
            
            # Check threshold
            if weight >= threshold:
                queue.appendleft(neighbor_uuid)
            else:
                queue.append(neighbor_uuid)
        
        # Fill current group from queue
        while queue and len(current_group) < group_size:
            next_uuid = queue.popleft()
            if next_uuid in unmatched:
                current_group.append(next_uuid)
                unmatched.remove(next_uuid)
                # Add to previous matches for both students
                if current_uuid not in previous_matches:
                    previous_matches[current_uuid] = set()
                if next_uuid not in previous_matches:
                    previous_matches[next_uuid] = set()
                previous_matches[current_uuid].add(next_uuid)
                previous_matches[next_uuid].add(current_uuid)
        
        # If current_group is full, save it
        if len(current_group) == group_size:
            group_id = f"G{len(groups) + 1}"
            groups[group_id] = current_group
        elif len(current_group) > 0:
            # Partial group - save anyway
            group_id = f"G{len(groups) + 1}"
            groups[group_id] = current_group
        
        # If queue empty and unmatched not empty, pick new start
        if not queue and unmatched:
            current_uuid = random.choice(list(unmatched))
            unmatched.remove(current_uuid)
            current_group = [current_uuid]
    
    # Store groups in tutorial
    tutorial.groups = groups
    tutorial.round += 1
    tutorial.state = "groups"
    
    # Update student group assignments
    for group_id, members in groups.items():
        for member_uuid in members:
            tutorial.students[member_uuid]["group"] = group_id
    
    return groups
```

### 7.5 Algorithm Parameters Per Round

| Round | Threshold | Previous Match Chance | |-------|-----------|----------------------| | 1 | 0.75 | 35% | | 2 | 0.65 | 35% | | 3 | 0.55 | 35% | | 4+ | 0.45 (min) | 35% |

### 7.6 Handling Edge Cases

- Fewer students than group size: Form one partial group with all students
- Odd number of students: Last group will have fewer members
- No matching students: Threshold decreases to allow looser matching
- All students already matched: Form groups randomly from unmatched

## 8. Backend-v2 File Structure

```
backend-v2/
├── main.py                    # Flask app entry point
├── pyproject.toml             # Dependencies
├── .env                       # Environment variables
├── app/
│   ├── __init__.py            # Flask app init, SocketIO init, JWT config
│   ├── enums.py               # State enums, attribute enums
│   ├── database/
│   │   ├── __init__.py        # SQLAlchemy init
│   │   └── models.py          # Staff model ONLY (no student models)
│   ├── routes/
│   │   ├── __init__.py        # Blueprint registration
│   │   ├── staff.py           # Staff REST endpoints (login, create tutorial, etc.)
│   │   └── student.py         # NO student REST endpoints (all via Socket.IO)
│   └── sockets/
│       ├── __init__.py        # In-memory tutorials dict, timer manager
│       ├── student.py         # Student Socket.IO handlers
│       ├── staff.py           # Staff Socket.IO handlers
│       ├── timer.py           # Timer management (intro + discussion)
│       ├── matching.py        # Group matching algorithm
│       └── utils.py           # Helper functions
└── tests/
    ├── conftest.py
    ├── helpers.py
    ├── test_staff.py
    ├── test_student.py
    └── test_timer.py
```

### 8.1 Backend-v2 Dependencies

```[project]
dependencies = [
    "flask>=3.0",
    "flask-socketio>=5.3",
    "flask-sqlalchemy>=3.1",
    "python-dotenv>=1.0",
    "pyjwt>=2.8",
    "bcrypt>=4.1",
    "gevent>=23.9",
    "gevent-websocket>=0.10.1",
]
```
### 8.2 Flask App Initialization (backend-v2/app/__init__.py)

```
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///study_mates.db"
    )
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["JWT_ALGORITHM"] = "HS256"
    app.config["JWT_EXPIRATION_HOURS"] = 24
    
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading",
                      ping_timeout=60, ping_interval=25)
    
    from app.routes.staff import staff_bp
    from app.routes.student import student_bp
    app.register_blueprint(staff_bp)
    app.register_blueprint(student_bp)
    
    from app.sockets.student import register_student_events
    from app.sockets.staff import register_staff_events
    register_student_events(socketio)
    register_staff_events(socketio)
    
    with app.app_context():
        db.create_all()
    
    return app, socketio
```

### 8.3 Staff REST Routes (backend-v2/app/routes/staff.py)

```
from flask import Blueprint, request, jsonify
import jwt
import bcrypt
from datetime import datetime, timedelta
from app import db, create_app
from app.database.models import Staff

staff_bp = Blueprint("staff", __name__)

@staff_bp.route("/api/staff/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    staff_member = Staff.query.filter_by(username=username).first()
    if not staff_member or not bcrypt.checkpw(
        password.encode("utf-8"), staff_member.password_hash.encode("utf-8")
    ):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Generate JWT
    payload = {
        "user_id": staff_member.id,
        "username": staff_member.username,
        "role": "staff",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(
            hours=int(app.config["JWT_EXPIRATION_HOURS"])
        )
    }
    token = jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm="HS256")
    
    staff_member.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({"token": token, "username": staff_member.username})
```

### 8.4 Student REST Routes (backend-v2/app/routes/student.py)

NO endpoints. All student operations are via Socket.IO events. This file should be minimal or empty, as students never make REST API calls.

## 9. Frontend-v2 File Structure

```
frontend-v2/
├── index.html
├── package.json
├── vite.config.js
├── vercel.json
├── src/
│   ├── App.jsx                  # Router, global state
│   ├── main.jsx                 # Entry point
│   ├── socket.js                # Socket.IO connection setup
│   ├── api/
│   │   └── staff.js             # Staff REST API calls (login, create tutorial)
│   ├── components/
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Input.jsx
│   │   ├── Modal.jsx
│   │   ├── Navbar.jsx
│   │   └── Timer.jsx            # NEW: Shared timer component
│   ├── context/
│   │   └── TutorialContext.jsx  # NEW: Global tutorial state via Socket.IO
│   ├── hooks/
│   │   └── useSocket.js         # NEW: Socket.IO event subscription hook
│   └── pages/
│       ├── NotFound.jsx
│       ├── staff/
│       │   ├── Login.jsx          # Staff login
│       │   ├── TutorialSetup.jsx  # Create tutorial
│       │   ├── LobbyLayout.jsx    # Lobby view
│       │   ├── GroupsLayout.jsx   # Groups view
│       │   └── DiscussionLayout.jsx # Discussion view
│       └── student/
│           ├── JoinTutorial.jsx   # Enter tutorial code
│           ├── EnterDetails.jsx   # Enter attributes (NEW: share toggles)
│           ├── LobbyLayout.jsx    # Lobby view
│           ├── GroupsLayout.jsx   # Groups view
│           └── DiscussionLayout.jsx # Discussion view
└── styles/
    └── index.css
```

### 9.1 Frontend-v2 Dependencies

```
{
  "dependencies": {
    "react": "^18.2",
    "react-dom": "^18.2",
    "react-router-dom": "^6.20",
    "socket.io-client": "^4.7",
    "axios": "^1.6"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2",
    "vite": "^5.0"
  }
}
```

### 9.2 Socket.IO Connection (frontend-v2/src/socket.js)

```
import { io } from "socket.io-client";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

let socket = null;

export function getSocket() {
    if (!socket) {
        socket = io(BACKEND_URL, {
            transports: ["websocket", "polling"],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 10,
            timeout: 20000
        });
    }
    return socket;
}

export function disconnectSocket() {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
}
```

### 9.3 Tutorial Context (frontend-v2/src/context/TutorialContext.jsx)

```
import { createContext, useContext, useState, useEffect, useRef } from "react";
import { getSocket } from "../socket";

const TutorialContext = createContext(null);

export function TutorialProvider({ children }) {
    const [tutorialCode, setTutorialCode] = useState(null);
    const [state, setState] = useState(null);
    const [students, setStudents] = useState([]);
    const [groups, setGroups] = useState(null);
    const [timer, setTimer] = useState(null);
    const [round, setRound] = useState(0);
    const [authenticated, setAuthenticated] = useState(false);
    const [studentUuid, setStudentUuid] = useState(null);
    const [studentName, setStudentName] = useState(null);
    const [currentDetails, setCurrentDetails] = useState({});
    const socketRef = useRef(null);

    useEffect(() => {
        socketRef.current = getSocket();
        const socket = socketRef.current;

        // Student events
        socket.on("authenticated", (data) => {
            setAuthenticated(true);
            setStudentUuid(data.uuid);
            setStudentName(data.name);
            setTutorialCode(data.tutorial_code);
        });

        socket.on("join_failed", (data) => {
            alert(data.reason);
        });

        socket.on("tutorial_state", (data) => {
            setState(data.state);
            setStudents(data.students);
            setGroups(data.groups);
            setTimer(data.timer);
            setRound(data.round);
        });

        socket.on("students_updated", (data) => {
            setStudents(data.students);
        });

        socket.on("groups_formed", (data) => {
            setGroups(data.groups);
            setRound(data.round);
        });

        socket.on("discussion_started", (data) => {
            setTimer({
                duration: data.intro_duration + data.discussion_duration,
                remaining: data.intro_duration,
                phase: "intro"
            });
        });

        socket.on("timer_update", (data) => {
            setTimer(data);
        });

        socket.on("timer_expired", (data) => {
            if (data.phase === "intro") {
                // Discussion timer starts
                setTimer({
                    ...timer,
                    remaining: timer.duration - timer.intro_duration,
                    phase: "discussion"
                });
            } else {
                // Discussion ended
                setTimer(null);
            }
        });

        socket.on("tutorial_ended", () => {
            setAuthenticated(false);
            setStudentUuid(null);
            setStudentName(null);
            setTutorialCode(null);
            setState(null);
            setStudents([]);
            setGroups(null);
            setTimer(null);
            setRound(0);
            setCurrentDetails({});
            // Redirect to home page
        });

        socket.on("error", (data) => {
            alert(data.message);
        });

        return () => {
            socket.off();
        };
    }, []);

    const joinTutorial = (code) => {
        socketRef.current.emit("join_tutorial", { code });
    };

    const updateDetails = (details) => {
        socketRef.current.emit("update_details", details);
        setCurrentDetails(details);
    };

    const enterTutorial = () => {
        socketRef.current.emit("enter_tutorial");
    };

    const startRound = () => {
        socketRef.current.emit("start_round");
    };

    const startDiscussion = () => {
        socketRef.current.emit("start_discussion");
    };

    const nextRound = () => {
        socketRef.current.emit("next_round");
    };

    const backToLobby = () => {
        socketRef.current.emit("back_to_lobby");
    };

    const endTutorial = () => {
        socketRef.current.emit("end_tutorial");
    };

    return (
        <TutorialContext.Provider value={{
            tutorialCode, state, students, groups, timer, round,
            authenticated, studentUuid, studentName, currentDetails,
            joinTutorial, updateDetails, enterTutorial,
            startRound, startDiscussion, nextRound, backToLobby, endTutorial
        }}>
            {children}
        </TutorialContext.Provider>
    );
}

export function useTutorial() {
    return useContext(TutorialContext);
}
```

### 9.4 EnterDetails Page (frontend-v2/src/pages/student/EnterDetails.jsx)

NEW: Share toggles per attribute

```
import { useState } from "react";
import { useTutorial } from "../../context/TutorialContext";

export default function EnterDetails() {
    const { updateDetails, enterTutorial, state, tutorialCode } = useTutorial();
    const [currentGPA, setCurrentGPA] = useState("");
    const [goalGPA, setGoalGPA] = useState("");
    const [availability, setAvailability] = useState({});
    const [sharedAttributes, setSharedAttributes] = useState([]);
    
    // Determine which attributes are available from tutorial state
    const availableAttributes = state?.available_attributes || [];
    
    const handleShareToggle = (attribute) => {
        if (sharedAttributes.includes(attribute)) {
            setSharedAttributes(sharedAttributes.filter(a => a !== attribute));
        } else {
            setSharedAttributes([...sharedAttributes, attribute]);
        }
    };
    
    const handleSubmit = () => {
        const details = {};
        if (currentGPA && availableAttributes.includes("currentGPA")) {
            details.currentGPA = parseFloat(currentGPA);
        }
        if (goalGPA && availableAttributes.includes("goalGPA")) {
            details.goalGPA = parseFloat(goalGPA);
        }
        if (Object.keys(availability).length > 0 && availableAttributes.includes("availability")) {
            details.availability = availability;
        }
        details.sharedAttributes = sharedAttributes;
        
        updateDetails(details);
        enterTutorial();
    };
    
    return (
        <div className="enter-details">
            <h2>Enter Your Details</h2>
            <p>Tutorial: {tutorialCode}</p>
            
            {availableAttributes.includes("currentGPA") && (
                <div className="field">
                    <label>Current GPA</label>
                    <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="7"
                        value={currentGPA}
                        onChange={(e) => setCurrentGPA(e.target.value)}
                    />
                    <label>
                        <input
                            type="checkbox"
                            checked={sharedAttributes.includes("currentGPA")}
                            onChange={() => handleShareToggle("currentGPA")}
                        />
                        Share with others
                    </label>
                </div>
            )}
            
            {availableAttributes.includes("goalGPA") && (
                <div className="field">
                    <label>Goal Grade</label>
                    <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="7"
                        value={goalGPA}
                        onChange={(e) => setGoalGPA(e.target.value)}
                    />
                    <label>
                        <input
                            type="checkbox"
                            checked={sharedAttributes.includes("goalGPA")}
                            onChange={() => handleShareToggle("goalGPA")}
                        />
                        Share with others
                    </label>
                </div>
            )}
            
            {availableAttributes.includes("availability") && (
                <div className="field">
                    <label>Availability</label>
                    {/* Availability picker component */}
                    <label>
                        <input
                            type="checkbox"
                            checked={sharedAttributes.includes("availability")}
                            onChange={() => handleShareToggle("availability")}
                        />
                        Share with others
                    </label>
                </div>
            )}
            
            <button onClick={handleSubmit}>Enter Tutorial</button>
        </div>
    );
}
```

### 9.5 Staff Tutorial Setup (frontend-v2/src/pages/staff/TutorialSetup.jsx)

NEW: Available attribute toggles

```
import { useState } from "react";
import { createTutorial } from "../../api/staff";

export default function TutorialSetup() {
    const [name, setName] = useState("");
    const [groupSize, setGroupSize] = useState(4);
    const [discussionDuration, setDiscussionDuration] = useState(600);
    const [availableAttributes, setAvailableAttributes] = useState([
        "currentGPA", "goalGPA", "availability"
    ]);
    const [createdCode, setCreatedCode] = useState(null);
    
    const handleAttributeToggle = (attribute) => {
        if (availableAttributes.includes(attribute)) {
            setAvailableAttributes(availableAttributes.filter(a => a !== attribute));
        } else {
            setAvailableAttributes([...availableAttributes, attribute]);
        }
    };
    
    const handleSubmit = async () => {
        const result = await createTutorial({
            name,
            groupSize,
            discussionDuration,
            availableAttributes
        });
        setCreatedCode(result.code);
    };
    
    return (
        <div className="tutorial-setup">
            <h2>Create Tutorial</h2>
            
            <div className="field">
                <label>Tutorial Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            
            <div className="field">
                <label>Group Size</label>
                <input type="number" min="2" max="10" value={groupSize} onChange={(e) => setGroupSize(e.target.value)} />
            </div>
            
            <div className="field">
                <label>Discussion Duration (seconds)</label>
                <input type="number" min="60" max="3600" value={discussionDuration} onChange={(e) => setDiscussionDuration(e.target.value)} />
            </div>
            
            <div className="field">
                <label>Available Attributes</label>
                {["currentGPA", "goalGPA", "availability"].map(attr => (
                    <label key={attr}>
                        <input
                            type="checkbox"
                            checked={availableAttributes.includes(attr)}
                            onChange={() => handleAttributeToggle(attr)}
                        />
                        {attr === "currentGPA" ? "Current GPA" : 
                         attr === "goalGPA" ? "Goal Grade" : "Availability"}
                    </label>
                ))}
            </div>
            
            <button onClick={handleSubmit}>Create Tutorial</button>
            
            {createdCode && (
                <div className="result">
                    <h3>Tutorial Created!</h3>
                    <p>Code: {createdCode}</p>
                    <p>Share this code with students</p>
                </div>
            )}
        </div>
    );
}
```

### 9.6 Staff API (frontend-v2/src/api/staff.js)

```
import axios from "axios";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

let staffToken = localStorage.getItem("staff_token");

export function getStaffToken() {
    return staffToken;
}

export function setStaffToken(token) {
    staffToken = token;
    localStorage.setItem("staff_token", token);
}

export function clearStaffToken() {
    staffToken = null;
    localStorage.removeItem("staff_token");
}

export async function login(username, password) {
    const response = await axios.post(`${BACKEND_URL}/api/staff/login`, {
        username,
        password
    });
    setStaffToken(response.data.token);
    return response.data;
}

export async function createTutorial(data) {
    const response = await axios.post(`${BACKEND_URL}/api/staff/create-tutorial`, data, {
        headers: { Authorization: `Bearer ${staffToken}` }
    });
    return response.data;
}

export async function endTutorial(code) {
    await axios.post(`${BACKEND_URL}/api/staff/end-tutorial`, { code }, {
        headers: { Authorization: `Bearer ${staffToken}` }
    });
}
```

## 10. Timer Management

### 10.1 Timer Architecture

The server manages all timers. The client only displays and reacts to timer events.

In backend-v2/app/sockets/timer.py
```
import time
import threading

class TutorialTimer:
    def __init__(self, tutorial_code, socketio):
        self.tutorial_code = tutorial_code
        self.socketio = socketio
        self.thread = None
        self.running = False
    
    def start_intro(self, duration=30):
        self.running = True
        self.remaining = duration
        self.phase = "intro"
        tutorials[self.tutorial_code]["timer"] = {
            "duration": duration,
            "remaining": duration,
            "running": True,
            "phase": "intro"
        }
        tutorials[self.tutorial_code]["timer"]["discussion_remaining"] = tutorials[self.tutorial_code]["discussion_duration"]
        
        self.thread = threading.Thread(target=self._tick, daemon=True)
        self.thread.start()
    
    def start_discussion(self, duration):
        self.running = True
        self.remaining = duration
        self.phase = "discussion"
        tutorials[self.tutorial_code]["timer"] = {
            "duration": duration,
            "remaining": duration,
            "running": True,
            "phase": "discussion"
        }
        
        self.thread = threading.Thread(target=self._tick, daemon=True)
        self.thread.start()
    
    def _tick(self):
        while self.running:
            time.sleep(1)
            if not self.running:
                break
            
            self.remaining -= 1
            tutorials[self.tutorial_code]["timer"]["remaining"] = self.remaining
            
            self.socketio.emit(
                "timer_update",
                {"remaining": self.remaining, "phase": self.phase},
                room=f"tutorial_{self.tutorial_code}"
            )
            
            if self.remaining <= 0:
                self.running = False
                tutorials[self.tutorial_code]["timer"]["running"] = False
                
                if self.phase == "intro":
                    # Auto-switch to discussion
                    tutorials[self.tutorial_code]["timer"]["phase"] = "discussion"
                    tutorials[self.tutorial_code]["timer"]["remaining"] = tutorials[self.tutorial_code]["discussion_duration"]
                    tutorials[self.tutorial_code]["timer"]["running"] = True
                    self.remaining = tutorials[self.tutorial_code]["discussion_duration"]
                    self.phase = "discussion"
                    
                    self.socketio.emit(
                        "timer_expired",
                        {"phase": "intro"},
                        room=f"tutorial_{self.tutorial_code}"
                    )
                    
                    # Start discussion timer
                    self.start_discussion(tutorials[self.tutorial_code]["discussion_duration"])
                    
                else:
                    # Discussion ended
                    self.socketio.emit(
                        "timer_expired",
                        {"phase": "discussion"},
                        room=f"tutorial_{self.tutorial_code}"
                    )
                    tutorials[self.tutorial_code]["state"] = "groups"
    
    def stop(self):
        self.running = False
```

### 10.2 Timer Flow

```
Staff clicks "Start Discussion"
    → Server sets state to "discussion"
    → Server starts intro timer (30s)
    → Server emits "discussion_started" with intro + discussion durations
    → Client displays 30s intro timer
    
30s elapsed (auto)
    → Server emits "timer_expired" with phase="intro"
    → Server automatically starts discussion timer
    → Server emits "timer_update" with discussion phase
    → Client displays discussion timer
    
Discussion duration elapsed (auto)
    → Server emits "timer_expired" with phase="discussion"
    → Server sets state to "groups"
    → Server re-emits "groups_formed"
    → Client displays groups
    → Staff chooses "next round" or "back to lobby"
```

## 11. CORS Configuration

### 11.1 Backend CORS (Flask-SocketIO)

In backend-v2/app/__init__.py
```
socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")
Note: cors_allowed_origins="*" is used for development. In production, replace with specific allowed origins:

socketio.init_app(app, cors_allowed_origins=["https://study-mates.vercel.app"], async_mode="threading")
```

### 11.2 Flask CORS (REST API)

Install: pip install flask-cors
```
from flask_cors import CORS

CORS(app, resources={r"/api/*": {"origins": ["https://study-mates.vercel.app"]}})
```

### 11.3 Frontend CORS (Vercel)

```
// frontend-v2/vercel.json
{
    "rewrites": [
        { "source": "/(.*)", "destination": "/index.html" }
    ]
}
```

### 11.4 Socket.IO CORS

Socket.IO handles its own CORS. The cors_allowed_origins parameter in socketio.init_app() controls which origins can connect via WebSocket.

## 12. Student Data Privacy

### 12.1 Data Lifecycle

Entry: Student data created when student joins tutorial (in-memory)
Storage: Data stored only in tutorials[code].students[uuid] dict
Sharing: Only attributes in shared_attributes list are visible to other students
Deletion: All data cleared when tutorial ends
Persistence: NO student data is ever written to database or disk

### 12.2 Auto-Expiration

In backend-v2/app/sockets/__init__.py
```
import time

def cleanup_expired_tutorials():
    """Run periodically (e.g., every 5 minutes) to clean up idle tutorials"""
    current_time = time.time()
    expired = []
    
    for code, tutorial in tutorials.items():
        if tutorial["ended"]:
            expired.append(code)
            continue
        
        # Auto-expire if idle for 60 minutes
        if current_time - tutorial["last_activity"] > 3600:
            tutorial["ended"] = True
            expired.append(code)
    
    for code in expired:
        del tutorials[code]

# Run cleanup every 5 minutes
import threading
def cleanup_loop():
    while True:
        time.sleep(300)
        cleanup_expired_tutorials()

threading.Thread(target=cleanup_loop, daemon=True).start()
```

### 12.3 No Persistent Student Storage

Critical: Student data MUST NOT be stored in any database, file, or external storage. All student data exists only in the in-memory tutorials dictionary during the active tutorial session.

## 13. Staff Login Page (frontend-v2/src/pages/staff/Login.jsx)

```
import { useState } from "react";
import { login } from "../../api/staff";

export default function Login() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        try {
            await login(username, password);
            // Navigate to tutorial setup
        } catch (err) {
            setError("Invalid credentials");
        }
    };
    
    return (
        <div className="staff-login">
            <h2>Staff Login</h2>
            <form onSubmit={handleSubmit}>
                <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                <button type="submit">Login</button>
            </form>
            {error && <p className="error">{error}</p>}
        </div>
    );
}
```

## 14. App Routing (frontend-v2/src/App.jsx)

```
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { TutorialProvider } from "./context/TutorialContext";
import { getStaffToken } from "./api/staff";
import Login from "./pages/staff/Login";
import TutorialSetup from "./pages/staff/TutorialSetup";
import LobbyLayout from "./pages/staff/LobbyLayout";
import GroupsLayout from "./pages/staff/GroupsLayout";
import DiscussionLayout from "./pages/staff/DiscussionLayout";
import JoinTutorial from "./pages/student/JoinTutorial";
import EnterDetails from "./pages/student/EnterDetails";
import StudentLobbyLayout from "./pages/student/LobbyLayout";
import StudentGroupsLayout from "./pages/student/GroupsLayout";
import StudentDiscussionLayout from "./pages/student/DiscussionLayout";
import NotFound from "./pages/NotFound";

function StaffProtectedRoute({ children }) {
    return getStaffToken() ? children : <Navigate to="/staff/login" />;
}

function StudentRoute({ children }) {
    // Student auth is via Socket.IO, not route-based
    // The TutorialContext handles this
    return children;
}

export default function App() {
    return (
        <BrowserRouter>
            <TutorialProvider>
                <Routes>
                    {/* Staff Routes */}
                    <Route path="/staff/login" element={<Login />} />
                    <Route path="/staff/setup" element={
                        <StaffProtectedRoute><TutorialSetup /></StaffProtectedRoute>
                    } />
                    <Route path="/staff/tutorial" element={
                        <StaffProtectedRoute><LobbyLayout /></StaffProtectedRoute>
                    } />
                    
                    {/* Student Routes */}
                    <Route path="/" element={<JoinTutorial />} />
                    <Route path="/enter-details" element={<EnterDetails />} />
                    <Route path="/lobby" element={<StudentLobbyLayout />} />
                    <Route path="/groups" element={<StudentGroupsLayout />} />
                    <Route path="/discussion" element={<StudentDiscussionLayout />} />
                    
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </TutorialProvider>
        </BrowserRouter>
    );
}
```

## 15. Implementation Checklist for AI

### Backend-v2 Tasks
[ ] Create backend-v2/ directory structure
[ ] Set up pyproject.toml with dependencies
[ ] Create main.py entry point
[ ] Create app/__init__.py with Flask + SocketIO + SQLAlchemy init
[ ] Create app/database/models.py with Staff model only
[ ] Create app/enums.py with state/attribute enums
[ ] Create app/routes/staff.py with login and tutorial management REST endpoints
[ ] Create app/routes/student.py (empty/minimal, no REST endpoints)
[ ] Create app/sockets/__init__.py with in-memory tutorials dict
[ ] Create app/sockets/student.py with all student Socket.IO event handlers
[ ] Create app/sockets/staff.py with all staff Socket.IO event handlers
[ ] Create app/sockets/timer.py with TutorialTimer class
[ ] Create app/sockets/matching.py with group matching algorithm
[ ] Create app/sockets/utils.py with helper functions
[ ] Set up JWT configuration and middleware
[ ] Configure CORS (Flask-CORS + SocketIO cors_allowed_origins)
[ ] Set up auto-cleanup for expired tutorials
[ ] Create test files in backend-v2/tests/

### Frontend-v2 Tasks
[ ] Create frontend-v2/ directory structure
[ ] Set up package.json with dependencies
[ ] Set up vite.config.js with React plugin
[ ] Create index.html
[ ] Create vercel.json
[ ] Create src/main.jsx
[ ] Create src/socket.js with Socket.IO connection
[ ] Create src/api/staff.js with staff REST API calls
[ ] Create src/context/TutorialContext.jsx with global tutorial state
[ ] Create src/hooks/useSocket.js with event subscription hook
[ ] Create src/components/Timer.jsx with shared timer component
[ ] Create src/components/Button.jsx, Card.jsx, Input.jsx, Modal.jsx, Navbar.jsx (adapt from v1)
[ ] Create src/pages/staff/Login.jsx
[ ] Create src/pages/staff/TutorialSetup.jsx with attribute toggles
[ ] Create src/pages/staff/LobbyLayout.jsx
[ ] Create src/pages/staff/GroupsLayout.jsx
[ ] Create src/pages/staff/DiscussionLayout.jsx
[ ] Create src/pages/student/JoinTutorial.jsx
[ ] Create src/pages/student/EnterDetails.jsx with share toggles
[ ] Create src/pages/student/LobbyLayout.jsx
[ ] Create src/pages/student/GroupsLayout.jsx
[ ] Create src/pages/student/DiscussionLayout.jsx
[ ] Create src/App.jsx with routing and TutorialProvider
[ ] Create src/styles/index.css (adapt from v1)
[ ] Ensure all student data display respects shared_attributes

### Critical Requirements
[ ] NO student data in database — in-memory only
[ ] Server generates all UUIDs — never client-side
[ ] No cookies for student auth — Socket.IO events only
[ ] JWT for staff authentication — stored in localStorage
[ ] Auto intro timer → auto discussion timer — no manual staff button for discussion start
[ ] Share toggles default to OFF — students must enable sharing
[ ] Available attributes toggled by staff — not all attributes always available
[ ] CORS-safe — cors_allowed_origins="*" for dev, specific origins for prod
[ ] Tutorial auto-expires after 60 min idle
[ ] All student data cleared on tutorial end
[ ] Socket.IO reconnection handled — students retain session on reconnect