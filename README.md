# BimBam ChatApp

A modern, full-stack real-time chat application with Google login, one-to-one and group conversations, friend system, message reactions, typing indicators, and online presence.

This repository contains:

- **Backend** – FastAPI, PostgreSQL, Redis, WebSockets
- **Frontend** – React + TypeScript + Vite + Tailwind + shadcn-style components
- **Infrastructure** – Docker Compose for local development

---

## Features

### Authentication & Accounts
- Sign in / sign up with **Google OAuth**
- JWT tokens stored in **HTTP-only cookies**
- First-time **username setup** after Google signup
- Basic account management (avatar, username, email display)

### Chat & Conversations
- **Direct messages (DMs)** between two users
- **Group conversations** with custom name and members
- Infinite scroll for message history
- Message status:
  - delivered / read flags
  - edited timestamp
- **Message editing**
- **Message reactions** with emoji:
  - reaction pills with counters
  - hover tooltip with list of users who reacted

### Social / Friends
- Search users by email / username
- Send / accept / reject **friend requests**
- List of friends and incoming / outgoing requests
- Conversations list shows last message and unread badge

### Real-Time UX
- WebSocket-based event system:
  - `message_send`, `message_edit`, `message_reaction`
  - `typing` events + typing indicator in UI
  - `presence` events (online / offline)
- Redis-backed **presence tracking**
- Unread count per conversation

### Developer Experience
- Backend:
  - FastAPI with Pydantic v2 schemas
  - SQLAlchemy 2.0 models
  - Alembic migrations
  - pytest + pytest-asyncio + testcontainers
- Frontend:
  - React 18 + TypeScript
  - Vite dev server
  - Tailwind CSS utility styling
  - Vitest + Testing Library
- Docker images for backend and frontend
- CI workflow via GitHub Actions (`.github/workflows/ci.yml`)

---

## Tech Stack

**Backend**
- Python 3.11
- FastAPI
- SQLAlchemy 2.0 + asyncpg
- Alembic
- PostgreSQL
- Redis
- Authlib (Google OAuth)
- python-jose / PyJWT (JWT)
- Uvicorn

**Frontend**
- React + TypeScript
- Vite
- Tailwind CSS
- lucide-react icons
- emoji-picker-react
- shadcn-style components

**Infrastructure**
- Docker / Docker Compose
- GitHub Actions CI

---

## Architecture Overview

# BimBam ChatApp

A modern, full-stack real-time chat application with Google login, one-to-one and group conversations, friend system, message reactions, typing indicators, and online presence.

This repository contains:

- **Backend** – FastAPI, PostgreSQL, Redis, WebSockets
- **Frontend** – React + TypeScript + Vite + Tailwind + shadcn-style components
- **Infrastructure** – Docker Compose for local development

---

## Features

### Authentication & Accounts
- Sign in / sign up with **Google OAuth**
- JWT tokens stored in **HTTP-only cookies**
- First-time **username setup** after Google signup
- Basic account management (avatar, username, email display)

### Chat & Conversations
- **Direct messages (DMs)** between two users
- **Group conversations** with custom name and members
- Infinite scroll for message history
- Message status:
  - delivered / read flags
  - edited timestamp
- **Message editing**
- **Message reactions** with emoji:
  - reaction pills with counters
  - hover tooltip with list of users who reacted

### Social / Friends
- Search users by email / username
- Send / accept / reject **friend requests**
- List of friends and incoming / outgoing requests
- Conversations list shows last message and unread badge

### Real-Time UX
- WebSocket-based event system:
  - `message_send`, `message_edit`, `message_reaction`
  - `typing` events + typing indicator in UI
  - `presence` events (online / offline)
- Redis-backed **presence tracking**
- Unread count per conversation

### Developer Experience
- Backend:
  - FastAPI with Pydantic v2 schemas
  - SQLAlchemy 2.0 models
  - Alembic migrations
  - pytest + pytest-asyncio + testcontainers
- Frontend:
  - React 18 + TypeScript
  - Vite dev server
  - Tailwind CSS utility styling
  - Vitest + Testing Library
- Docker images for backend and frontend
- CI workflow via GitHub Actions (`.github/workflows/ci.yml`)

---

## Tech Stack

**Backend**
- Python 3.11
- FastAPI
- SQLAlchemy 2.0 + asyncpg
- Alembic
- PostgreSQL
- Redis
- Authlib (Google OAuth)
- python-jose / PyJWT (JWT)
- Uvicorn

**Frontend**
- React + TypeScript
- Vite
- Tailwind CSS
- lucide-react icons
- emoji-picker-react
- shadcn-style components

**Infrastructure**
- Docker / Docker Compose
- GitHub Actions CI

---

## Architecture Overview

- **Backend API**: `http://localhost:8000/api/v1`
  - REST endpoints for auth, users, friends, conversations, messages
  - WebSocket endpoint at `ws://localhost:8000/ws`
- **Frontend SPA**: `http://localhost:5173`
  - Uses `VITE_API_URL` to talk to the backend (`/api/v1`)
  - Uses `VITE_WS_URL` (or same origin) for WebSocket

Data stores:
- **PostgreSQL**: persistent data (users, conversations, messages, friends, friend_requests, reactions, etc.)
- **Redis**: presence, online users, some unread/unseen tracking

---

## Getting Started

### Prerequisites

- Docker & Docker Compose **or**
- Python 3.11+, Node 18+/22+, PostgreSQL, Redis

---

## Option A — Run with Docker Compose (recommended)

From the repository root:

1. Create environment file for backend

   The Docker Compose file expects a `.env` at the repository root. You can start from the example:

```powershell
cp backend/.env.example .env
```

2. Start the stack

```powershell
docker compose up --build
```

Services after startup:
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

---

## Option B — Run Backend & Frontend Locally (without Docker)

### Backend

1. Create virtualenv & install dependencies

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# or: source .venv/bin/activate  # macOS / Linux
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure environment

Copy the example file and edit values as needed:

```powershell
cp .env.example .env
```

Minimal `.env` example (adapt values for your environment):

```text
ENV=development
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379/0

DATABASE__DB_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bimbam_chat
DATABASE__DB_HOST=localhost
DATABASE__DB_PORT=5432
DATABASE__DB_USER=postgres
DATABASE__DB_PASSWORD=postgres
DATABASE__DB_NAME=bimbam_chat

AUTH__GOOGLE_CLIENT_ID=your_google_client_id
AUTH__GOOGLE_CLIENT_SECRET=your_google_client_secret
AUTH__JWT_SECRET_KEY=super_super_secret_key
AUTH__ACCESS_TOKEN_EXPIRE_MINUTES=1440
AUTH__FRONTEND_ORIGIN=http://localhost:5173
AUTH__JWT_ALGORITHM=HS256
```

3. Create database & run migrations

Create the database in PostgreSQL, then run:

```powershell
cd backend
alembic upgrade head
```

4. Run the backend server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

1. Install dependencies

```powershell
cd frontend
npm install
```

2. Configure environment

Copy or create an `.env` file in `frontend/` with:

```text
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

3. Run the dev server

```powershell
npm run dev
```

By default Vite serves at `http://localhost:5173`.

---

## Google OAuth Configuration

To enable Google login:

1. Go to Google Cloud Console → Credentials
2. Create an OAuth 2.0 Client ID (Web application)
3. Add Authorized JavaScript origins for local dev:

```
http://localhost:5173
```

4. Add Authorized redirect URI:

```
http://localhost:8000/api/v1/auth/google/callback
```

5. Put credentials into the backend `.env`:

```text
AUTH__GOOGLE_CLIENT_ID=your_google_client_id
AUTH__GOOGLE_CLIENT_SECRET=your_google_client_secret
AUTH__FRONTEND_ORIGIN=http://localhost:5173
```

The frontend uses these endpoints for Google auth flows:

- `GET {API_URL}/api/v1/auth/google/login?mode=login` — sign in
- `GET {API_URL}/api/v1/auth/google/login?mode=signup` — sign up

On success the backend sets an HTTP-only access token cookie and redirects back to `AUTH__FRONTEND_ORIGIN`.

---

## Folder Structure (high-level)

```
.
├── backend/
│   ├── app/
│   │   ├── api/        # v1 routers, WebSocket endpoint, error handling
│   │   ├── core/       # Settings, config
│   │   ├── db/         # Session, base
│   │   ├── models/     # SQLAlchemy models
│   │   ├── repositories/# Data access layer
│   │   ├── services/   # Business logic
│   │   ├── schemas/    # Pydantic DTOs
│   │   ├── utils/      # JWT, errors, etc.
│   │   └── websockets/ # Connection manager, events
│   ├── alembic/        # DB migrations
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/            # React + TS app
│   ├── index.css       # Tailwind styles
│   └── package.json
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## Running Tests

### Backend

Run tests from the `backend/` directory:

```powershell
cd backend
pytest
```

```text
app\api\v1\__init__.py                                            4      0   100%
app\api\v1\deps.py                                               59      9    85%   56-57, 60-64, 70-71
app\api\v1\error_handler.py                                      36      8    78%   18, 22, 29, 35, 47, 53, 59-64
app\api\v1\routers\__init__.py                                    2      0   100%
app\api\v1\routers\auth.py                                       65     32    51%   34-39, 42-71, 83-123
app\api\v1\routers\conversations_router.py                       22      3    86%   43-48, 62
app\api\v1\routers\debug_router.py                               31     20    35%   27-97
app\api\v1\routers\friend_request.py                             31      6    81%   29, 47, 63, 79, 91, 103
app\api\v1\routers\friends.py                                    23      7    70%   54-67
app\api\v1\routers\messages.py                                   33     12    64%   26-27, 36-37, 48-49, 59-60, 70-71, 80-81
app\api\v1\routers\users.py                                      27     12    56%   19-20, 32-35, 47-50, 59-60
app\api\v1\routes_handler.py                                     10      0   100%
app\api\v1\ws.py                                                 89     10    89%   33, 36-37, 78-79, 88-91, 97
app\core\__init__.py                                              0      0   100%
app\core\config.py                                               14      0   100%
app\core\redis_client.py                                         97     69    29%   25, 29, 33, 37-44, 48-55, 62-64, 68-72, 80-83, 87-90, 94-98, 108-112, 119-123, 130-136, 140-154
app\core\settings\__init__.py                                     0      0   100%
app\core\settings\auth_settings.py                                9      0   100%
app\core\settings\database_settings.py                            9      0   100%
app\db\__init__.py                                                8      0   100%
app\db\base.py                                                    3      0   100%
app\db\base_class.py                                              3      3     0%   1-9
app\db\init_db.py                                                16     10    38%   13-18, 25-28
app\db\session.py                                                21      4    81%   16-19
app\main.py                                                      45      5    89%   27, 45, 70, 75, 81
app\models\__init__.py                                            7      0   100%
app\models\conversation.py                                       14      0   100%
app\models\conversation_member.py                                19      0   100%
app\models\enums.py                                               6      0   100%
app\models\friend_request.py                                     17      0   100%
app\models\friendship.py                                         16      0   100%
app\models\message.py                                            20      0   100%
app\models\message_edit.py                                       16      0   100%
app\models\message_reaction.py                                   16      0   100%
app\models\user.py                                               22      0   100%
app\repositories\__init__.py                                      0      0   100%
app\repositories\conversation_repository.py                      78     25    68%   35, 87-89, 111-125, 152, 158-173, 181-185
app\repositories\friend_request_repository.py                    39      7    82%   69-70, 106, 110-113
app\repositories\friendship_repository.py                        23      0   100%
app\repositories\message_reaction_repository.py                  65     49    25%   18-41, 44-55, 59-65, 68-70, 73-85, 92-103
app\repositories\message_repository.py                           82     33    60%   41, 63-70, 124-126, 145-150, 153-175, 178-183
app\repositories\user_repository.py                              52     25    52%   23-26, 29-35, 44-56, 79-84, 87-90, 93-98, 103-108
app\schemas\__init__.py                                           0      0   100%
app\schemas\conversation\__init__.py                              0      0   100%
app\schemas\conversation\conversation_create.py                   7      0   100%
app\schemas\conversation\conversation_preview.py                 14      0   100%
app\schemas\conversation\conversation_read.py                    12      0   100%
app\schemas\conversation_member\__init__.py                       0      0   100%
app\schemas\conversation_member\conversation_member_read.py      15      0   100%
app\schemas\friend_request\__init__.py                            0      0   100%
app\schemas\friend_request\friend_request_create.py               3      0   100%
app\schemas\friend_request\friend_request_read.py                11     11     0%   1-16
app\schemas\friend_request\friend_request_response.py            12      0   100%
app\schemas\friendship\__init__.py                                0      0   100%
app\schemas\friendship\friendship.py                             19      0   100%
app\schemas\message\__init__.py                                   0      0   100%
app\schemas\message\message_base.py                               6      6     0%   1-9
app\schemas\message\message_create.py                             5      5     0%   1-8
app\schemas\message\message_edit.py                              17      0   100%
app\schemas\message\message_page.py                              10      0   100%
app\schemas\message\message_read.py                              18      0   100%
app\schemas\message\message_update.py                             3      3     0%   1-5
app\schemas\message_reaction\message_reaction.py                 19      0   100%
app\schemas\presence\__init__.py                                  0      0   100%
app\schemas\presence\presence_status.py                           8      8     0%   1-11
app\schemas\typing\typing_status.py                               7      0   100%
app\schemas\user\__init__.py                                      0      0   100%
app\schemas\user\user_base.py                                     6      0   100%
app\schemas\user\user_create.py                                   9      9     0%   1-13
app\schemas\user\user_read.py                                    10      0   100%
app\schemas\user\user_response.py                                 8      0   100%
app\schemas\websocket\__init__.py                                 0      0   100%
app\schemas\websocket\envelope.py                                 9      0   100%
app\schemas\websocket\error_events.py                             7      0   100%
app\schemas\websocket\event_types.py                             11      0   100%
app\schemas\websocket\message_events.py                          41      0   100%
app\services\__init__.py                                          0      0   100%
app\services\conversation_service.py                            103     67    35%   33, 37, 42-63, 66-73, 76-83, 86, 90-110, 126, 129-147, 157-176, 185-192, 195-203
app\services\friend_request_service.py                           70     38    46%   54-92, 97-109, 114-123, 128-137, 141, 145
app\services\friendship_service.py                               21      1    95%   32
app\services\message_service.py                                 126     89    29%   32-34, 39-42, 52, 56-67, 70, 79-95, 106-134, 144-151, 165-194, 206-220, 223-233, 236-247, 250-259, 262-269, 272-279
app\services\presence_service.py                                 14      4    71%   14, 17, 20, 23
app\services\user_service.py                                     58     38    34%   13, 16, 24, 27, 30, 40-49, 52, 55-56, 59-71, 74-77, 82-88, 93-98
app\utils\__init__.py                                             0      0   100%
app\utils\errors\base_app_exception.py                            5      0   100%
app\utils\errors\database_exception.py                            4      1    75%   7
app\utils\errors\forbidden_exception.py                           4      1    75%   10
app\utils\errors\resource_not_found.py                            4      1    75%   7
app\utils\errors\unauthorized_exception.py                        4      1    75%   8
app\utils\errors\user_not_found_exception.py                      4      1    75%   7
app\utils\errors\validation_exception.py                          4      0   100%
app\utils\jwt_utils.py                                           17      0   100%
app\websockets\__init__.py                                        0      0   100%
app\websockets\connection_manager.py                             79     22    72%   33, 45-51, 73-75, 93-97, 101-106
app\websockets\events.py                                        223    132    41%   38, 72-76, 105-108, 111-112, 127-130, 178-228, 243-331, 348-351, 364-373, 377-378, 399-452, 476, 478, 481-484
-------------------------------------------------------------------------------------------
TOTAL                                                          2221    810    64%
56 passed, 1 skipped in 8.80s
```
The test suite uses `pytest`, `pytest-asyncio`, and `testcontainers` where needed.

### Frontend

From `frontend/`:

```powershell
cd frontend
npm test
```

Uses `vitest` + Testing Library.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

If you'd like, I can add a `.env.example` (backend + frontend) or validate the README changes against the repo configs.
