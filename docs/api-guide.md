# API Guide

Swagger UI is available at `/docs` in local debug mode.

Authentication:

```http
POST /auth/login
```

Use the returned bearer token for `/admin/*`.

Voice:

- `POST /voice/start`
- `POST /voice/speak`
- `POST /voice/audio`
- `POST /voice/end`
- `POST /voice/event`

HTTP-only smoke test:

1. Start a session with `POST /voice/start`.
2. Send text to `POST /voice/speak` to receive playable TTS audio.
3. Send a WAV file to `POST /voice/audio` to run STT -> LLM -> TTS and receive playable audio.

Zoiper remains a SIP/RTP client. It does not call HTTP or WebSocket directly; FreeSWITCH bridges Zoiper RTP into Dograh.

Calls:

- `GET /calls`
- `GET /calls/{id}`
- `GET /transcripts/{call_id}`
- `GET /summary/{call_id}`

Admin:

- `GET /admin/dashboard`
- `GET /admin/live-calls`
- `GET /admin/analytics`
- `GET /admin/providers`
- `GET /admin/settings`
- `GET /admin/system`
- `GET /admin/logs`
- `POST /admin/simulate-outbound-call`
