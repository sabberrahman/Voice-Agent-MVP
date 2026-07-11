# Development Guide

The API uses Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, Ruff, Black, and Pytest.

Local API setup:

```powershell
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ruff check app
black app
pytest
```

Migrations:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Keep provider implementations behind the interfaces in `app/providers`. The Voice Orchestrator should never import concrete STT, LLM, or TTS provider clients directly.
