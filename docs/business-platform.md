# Business Platform

Prompt 3 adds the internal SaaS management layer without replacing the telephony or AI pipeline.

## Dashboard

The Next.js dashboard runs at `http://localhost:3000`.

Demo credentials:

- Email: `admin@voxagent.local`
- Password: `admin123`

Pages:

- Dashboard
- Live Calls
- Call History
- Customers
- Campaigns
- Knowledge Base
- Analytics
- Providers
- Settings
- Logs
- System

## API

Admin endpoints are under `/admin/*` and require a bearer token from `/auth/login`.

Important endpoints:

- `GET /admin/dashboard`
- `GET /admin/live-calls`
- `GET /admin/analytics`
- `GET /admin/providers`
- `GET /admin/settings`
- `GET /admin/system`
- `GET /admin/call-details/{call_id}`

The dashboard uses React Query polling so live calls and health state update during investor demos.

## Multi-Tenancy

The data model already scopes core resources by tenant. Prompt 3 prepares the UI and API for future tenant-specific customers, calls, prompts, providers, and knowledge bases, but does not add full tenant onboarding.
