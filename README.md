# VoxAgent MVP Foundation

Production-oriented local foundation for a multi-tenant, provider-agnostic AI voice platform.

This first prompt intentionally implements infrastructure and architecture only:

- FastAPI Voice Orchestrator API
- PostgreSQL, Redis, Nginx
- FreeSWITCH with SIP extensions `1001` and `1002`
- Dograh routing bridge placeholder
- Provider interfaces for STT, LLM, and TTS
- SQLAlchemy models and Alembic migration for future-ready voice SaaS data
- UTF-8 and Bangla-first configuration

The MVP now includes the AI voice pipeline and a polished internal SaaS dashboard. GPU, PSTN, IPTSP, SBC, Kubernetes, Kamailio, and real SIP trunks remain future phases.

## Quick Start

```powershell
docker compose up --build
```

This starts every service and runs API database migrations automatically.

Optional development migration rerun:

```powershell
.\scripts\migrate.ps1
```

Useful endpoints:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:3000`
- Nginx gateway: `http://localhost:8080`
- Health: `http://localhost:8000/health`
- Ready: `http://localhost:8000/ready`
- Providers: `http://localhost:8000/providers`
- Audio pipeline: `POST http://localhost:8000/voice/audio`
- Metrics: `http://localhost:8000/metrics`
- Dograh bridge health: `http://localhost:8010/health`

Dashboard login:

- Email: `admin@voxagent.local`
- Password: `admin123`

## Zoiper Setup

Create two SIP accounts:

Extension `1001`

- User: `1001`
- Password: `1001pass`
- Domain/Host: your Docker host IP, usually `127.0.0.1`
- Transport: UDP
- Port: `5060`

Extension `1002`

- User: `1002`
- Password: `1002pass`
- Domain/Host: your Docker host IP, usually `127.0.0.1`
- Transport: UDP
- Port: `5060`

Call `1002` from `1001`, or `1001` from `1002`. Recordings are stored in the Docker volume `voxagent-mvp_freeswitch_recordings`.

## Architecture

Dograh routes session events to the Voice Orchestrator. Dograh does not call STT, LLM, or TTS providers.

```text
SIP softphone
  -> FreeSWITCH
  -> Dograh routing bridge
  -> Voice Orchestrator
  -> STT adapter interface
  -> Context Builder
  -> LLM adapter interface
  -> Tool Layer
  -> Memory
  -> TTS adapter interface
```

## Provider Agnostic Design

Business logic depends on abstract provider contracts only:

- `services/api/app/providers/stt/base.py`
- `services/api/app/providers/llm/base.py`
- `services/api/app/providers/tts/base.py`

Provider selection is configuration-driven with:

- `DEFAULT_STT_PROVIDER`
- `DEFAULT_LLM_PROVIDER`
- `DEFAULT_TTS_PROVIDER`

Prompt 2 adds the active pipeline for Groq STT, Claude LLM, Cartesia TTS, plus OpenAI LLM/TTS alternatives. See [docs/ai-pipeline.md](docs/ai-pipeline.md).

## Project Structure

See [docs/folder-structure.md](docs/folder-structure.md), [docs/docker-setup.md](docs/docker-setup.md), [docs/end-to-end-zoiper.md](docs/end-to-end-zoiper.md), and [docs/environment.md](docs/environment.md).

## Development

Format and lint inside `services/api`:

```powershell
pip install -e ".[dev]"
ruff check app
black app
pytest
```
