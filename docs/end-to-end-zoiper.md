# End-to-End Docker + Zoiper Test

Start the full local stack:

```bash
bash ./scripts/dev.sh
```

This detects the current LAN/WiFi IP, updates `.env`, prints Zoiper copy-paste settings, then starts PostgreSQL, Redis, API, Dograh, Web, FreeSWITCH, and Nginx. The API runs database migrations automatically before it starts.

Where things run:

- Web dashboard: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/health`
- Providers: `http://localhost:8000/providers`
- Dograh health: `http://localhost:8010/health`
- Dograh WebSocket bridge: `ws://localhost:8010/ws`
- API WebSocket: `ws://localhost:8000/voice/ws`
- Nginx gateway: `http://localhost:8080`
- SIP server: the `ZOIPER_HOST_IP` printed at startup, port `5060`

Check services:

```powershell
docker compose ps
```

Dashboard login:

- Email: `admin@voxagent.local`
- Password: `admin123`

Seed local Zoiper test customers:

```powershell
$token = (Invoke-RestMethod -Method Post http://localhost:8000/auth/login -Body (@{email="admin@voxagent.local";password="admin123"} | ConvertTo-Json) -ContentType "application/json").access_token
Invoke-RestMethod -Method Post http://localhost:8000/admin/seed-zoiper-customers -Headers @{Authorization="Bearer $token"}
```

This creates customer rows for phone numbers `1001` and `1002`. You only need one registered Zoiper user for a human-to-AI inbound or outbound test; the second extension is for softphone-to-softphone checks.

Zoiper setup:

- Account 1 user: `1001`
- Account 1 password: `1001pass`
- Account 2 user: `1002`
- Account 2 password: `1002pass`
- Host/domain: use the `Host / Domain` value printed by `docker compose up --build`
- Port: `5060`
- Transport: UDP

Inbound human-to-AI call:

1. Register Zoiper account `1001`.
2. Call `7000` from `1001`.
3. FreeSWITCH answers, starts `mod_audio_stream`, and streams caller audio to `ws://dograh:8010/freeswitch/media`.
4. Dograh keeps one WebSocket open to `ws://api:8000/voice/ws`.
5. Redis stores live call state during the call; PostgreSQL is written when the call ends.

Outbound AI-to-human call:

1. Register Zoiper account `1001`.
2. Trigger the outbound call:

```powershell
$token = (Invoke-RestMethod -Method Post http://localhost:8000/auth/login -Body (@{email="admin@voxagent.local";password="admin123"} | ConvertTo-Json) -ContentType "application/json").access_token
Invoke-RestMethod -Method Post http://localhost:8000/admin/start-outbound-zoiper/1001 -Headers @{Authorization="Bearer $token"}
```

3. FreeSWITCH originates a call to `user/1001`.
4. When `1001` answers, FreeSWITCH sends the answered channel to extension `7000`, which starts the same AI agent media stream.
5. Dograh buffers short FreeSWITCH media frames into AI chunks, sends them through the API WebSocket, and returns TTS audio to the call.

Extension-to-extension test call:

1. Register both Zoiper accounts.
2. Call `1002` from `1001`, or `1001` from `1002`.
3. Watch logs with `docker compose logs -f api dograh freeswitch`.
4. Open the dashboard calls page: `http://localhost:3000/calls`.

For local testing, `1001` can be the human caller/receiver. `1002` is only needed when you want a second softphone to test person-to-person SIP behavior.

AI provider setup currently uses:

- STT: Groq
- LLM: Groq
- TTS: Cartesia
- Default Cartesia voice: Rubul male

For STT + LLM-only testing, set both flags to false and restart `api` and `dograh`:

```env
ENABLE_TTS=false
DOGRAH_ENABLE_TTS=false
```

In this mode Zoiper will connect and stay silent, while caller audio is still sent through STT and the LLM response is saved in transcripts/live call state.

Stop everything:

```powershell
docker compose down
```
