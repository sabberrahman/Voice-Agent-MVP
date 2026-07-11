# Docker Setup

Start everything:

```powershell
docker compose up --build
```

The API runs database migrations automatically before starting.

Check containers:

```powershell
docker compose ps
```

Health checks:

```powershell
curl http://localhost:8000/health
curl http://localhost:8080/ready
curl http://localhost:8010/health
```

FreeSWITCH CLI:

```powershell
docker compose exec freeswitch fs_cli
```

Recordings are stored in the named Docker volume `voxagent-mvp_freeswitch_recordings`.

For a short end-to-end softphone test, see [end-to-end-zoiper.md](end-to-end-zoiper.md).
