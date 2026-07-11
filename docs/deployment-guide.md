# Deployment Guide

The MVP remains Docker Compose based.

Local:

```powershell
docker compose up --build
```

Production preparation checklist:

- Replace demo credentials.
- Set a strong `APP_SECRET_KEY`.
- Use managed PostgreSQL or hardened persistent storage.
- Use managed Redis or a password-protected Redis instance.
- Terminate HTTPS at Nginx or an upstream load balancer.
- Move provider keys into a secret manager.
- Back up recordings to S3-compatible storage.
- Add real SIP trunking and carrier failover.
- Enable Prometheus, Grafana, Loki, Sentry, and OpenTelemetry.

The architecture is intentionally ready for real SIP trunks and self-hosted inference without changing business logic.
