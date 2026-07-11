# Observability

The platform currently exposes app-level JSON logs, request correlation IDs, `/metrics`, `/ready`, and `/admin/system`.

Prepared future integrations:

- Prometheus: scrape `/metrics` or a future OpenMetrics endpoint.
- Grafana: dashboard for call volume, latency, success rate, provider usage, and infrastructure health.
- Loki: collect structured JSON logs from API, Dograh bridge, Nginx, and FreeSWITCH.
- Sentry: capture unhandled exceptions and request context.
- OpenTelemetry: trace call lifecycle from Dograh event to STT, LLM, TTS, and persistence.

These are placeholders by design; Prompt 3 does not add extra infrastructure services.
