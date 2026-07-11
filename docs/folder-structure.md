# Folder Structure

```text
.
├── docker-compose.yml
├── services
│   ├── api
│   │   ├── app
│   │   │   ├── api
│   │   │   ├── config
│   │   │   ├── core
│   │   │   ├── db
│   │   │   ├── models
│   │   │   ├── providers
│   │   │   ├── voice
│   │   │   ├── telephony
│   │   │   ├── memory
│   │   │   ├── context
│   │   │   ├── events
│   │   │   └── workers
│   │   └── alembic
│   ├── dograh
│   ├── pbx
│   ├── nginx
│   └── shared
├── docs
└── scripts
```

The API follows clean architecture boundaries: routes depend on services/orchestrators, orchestrators depend on interfaces, and infrastructure implementations stay replaceable.
