# Feed Indexer

An AI-powered news aggregator that clusters articles from 15+ RSS feeds into deduplicated Events, analyzes them with Gemini, and presents a calm, organized feed.

## Quick Start

### 1. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get a free Gemini API key at https://aistudio.google.com

### 3. Start the backend

```bash
cd backend
uvicorn app.main:app --reload
```

The server starts at http://localhost:8000  
On startup it automatically fetches all feeds and runs AI analysis.

### 4. Open the frontend

Open `frontend/index.html` in your browser.

> **Note**: Because the JS uses ES modules (`import/export`), you need to serve
> the frontend from a local server rather than opening the file directly.
> The easiest way:
> ```bash
> cd frontend
> python -m http.server 3000
> ```
> Then visit http://localhost:3000

---

## Project Structure

```
feed-indexer/
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI entry point
│   │   ├── config.py        ← All settings (reads from .env)
│   │   ├── database.py      ← SQLAlchemy setup
│   │   ├── models/          ← DB models (Event, Article, UserPreferences)
│   │   ├── schemas/         ← Pydantic schemas (API I/O)
│   │   ├── providers/       ← RSS feed provider system
│   │   │   ├── base.py      ← NewsProvider ABC
│   │   │   ├── registry.py  ← All active providers registered here
│   │   │   └── feeds/       ← One file per source group
│   │   ├── ingestion/       ← Fetcher, normalizer, pipeline
│   │   ├── processing/      ← TF-IDF deduplication
│   │   ├── ai/              ← Gemini analysis
│   │   ├── ranking/         ← Scoring + sectioning
│   │   └── api/             ← FastAPI route handlers
│   └── requirements.txt
└── frontend/
    ├── index.html           ← Homepage (sectioned feed)
    ├── event.html           ← Event detail page
    ├── settings.html        ← User preferences
    ├── css/                 ← variables, main, components
    └── js/                  ← api, home, event, settings
```

---

## Adding a New RSS Source

1. Create a file in `backend/app/providers/feeds/` (or add to an existing one):

```python
from app.providers.base import NewsProvider, FeedInfo

class MyNewsProvider(NewsProvider):
    @property
    def name(self) -> str:
        return "My News"

    @property
    def feeds(self):
        return [
            FeedInfo(
                name="My News – World",
                url="https://mynews.com/rss/world.xml",
                category="world",
                country="world",
            )
        ]
```

2. Register it in `backend/app/providers/registry.py`:
```python
from app.providers.feeds.my_file import MyNewsProvider
PROVIDERS = [..., MyNewsProvider()]
```

Done. The ingestion pipeline picks it up automatically.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/events/` | Sectioned homepage feed |
| GET | `/api/events/{id}` | Full event detail |
| POST | `/api/ingest` | Trigger manual ingestion |
| GET | `/api/feeds/` | List all providers |
| GET | `/api/preferences/` | Get user preferences |
| PUT | `/api/preferences/` | Update user preferences |
| GET | `/api/health` | Health check |

Interactive API docs: http://localhost:8000/docs

---

## Swapping to PostgreSQL

Change one line in `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/feedindexer
```

Install the driver: `pip install psycopg2-binary`

The SQLAlchemy models are already Postgres-compatible — no other changes needed.
