# API Guide

Swagger UI is available at `/docs` in local debug mode.

Authentication:

```http
POST /auth/login
```

Use the returned bearer token for `/admin/*`.

Voice:

- `POST /voice/start`
- `POST /voice/audio`
- `POST /voice/end`
- `POST /voice/event`

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
