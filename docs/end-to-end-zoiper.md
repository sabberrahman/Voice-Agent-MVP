# End-to-End Docker + Zoiper Test

Start the full local stack:

```powershell
docker compose up --build
```

This starts PostgreSQL, Redis, API, Dograh, Web, FreeSWITCH, and Nginx. The API runs database migrations automatically before it starts.

Where things run:

- Web dashboard: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- Providers: `http://localhost:8000/providers`
- Dograh health: `http://localhost:8010/health`
- Nginx gateway: `http://localhost:8080`
- SIP server: `127.0.0.1:5060`

Check services:

```powershell
docker compose ps
```

Dashboard login:

- Email: `admin@voxagent.local`
- Password: `admin123`

Zoiper setup:

- Account 1 user: `1001`
- Account 1 password: `1001pass`
- Account 2 user: `1002`
- Account 2 password: `1002pass`
- Host/domain: `127.0.0.1`
- Port: `5060`
- Transport: UDP

Test call:

1. Register both Zoiper accounts.
2. Call `1002` from `1001`, or `1001` from `1002`.
3. Watch logs with `docker compose logs -f api dograh freeswitch`.
4. Open the dashboard calls page: `http://localhost:3000/calls`.

AI provider setup currently uses:

- STT: Groq
- LLM: Groq
- TTS: Cartesia
- Default Cartesia voice: Rubul male

Stop everything:

```powershell
docker compose down
```
