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

Recommended cross-platform starter for Git Bash, Linux, or macOS:

```bash
bash ./scripts/dev.sh
```

This detects the current LAN/WiFi IP, updates `.env`, prints Zoiper copy-paste settings, then starts Docker Compose.

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
- WebSocket audio pipeline: `ws://localhost:8000/voice/ws`
- Dograh WebSocket bridge: `ws://localhost:8010/ws`
- Legacy audio pipeline: `POST http://localhost:8000/voice/audio`
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
- Domain/Host: the `Host / Domain` value printed by `docker compose up --build`
- Transport: UDP
- Port: `5060`

Extension `1002`

- User: `1002`
- Password: `1002pass`
- Domain/Host: the `Host / Domain` value printed by `docker compose up --build`
- Transport: UDP
- Port: `5060`

Call `7000` from `1001` to reach the AI agent. Call `1002` from `1001`, or `1001` from `1002`, only when you want to test human-to-human SIP registration. Recordings are stored in the Docker volume `voxagent-mvp_freeswitch_recordings`.

Outbound AI-to-human test:

```powershell
$token = (Invoke-RestMethod -Method Post http://localhost:8000/auth/login -Body (@{email="admin@voxagent.local";password="admin123"} | ConvertTo-Json) -ContentType "application/json").access_token
Invoke-RestMethod -Method Post http://localhost:8000/admin/start-outbound-zoiper/1001 -Headers @{Authorization="Bearer $token"}
```

## Architecture

Dograh routes session events to the Voice Orchestrator. Dograh does not call STT, LLM, or TTS providers.

```text
SIP softphone
  -> FreeSWITCH
  -> mod_audio_stream
  -> Dograh WebSocket bridge
  -> Voice Orchestrator
  -> STT adapter interface
  -> Context Builder
  -> LLM adapter interface
  -> Tool Layer
  -> Memory
  -> TTS adapter interface
```

Redis is the live-call memory layer. During a call, call metadata, events, transcript turns, recent conversation history, and live state are written to Redis first. PostgreSQL persistence is deferred until `/voice/end`, so database writes are not on the audio turn latency path.

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
