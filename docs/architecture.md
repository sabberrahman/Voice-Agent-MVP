# Architecture

VoxAgent is designed as a clean, provider-agnostic voice SaaS foundation. The telephony layer emits call/session events, while business workflows live in the Voice Orchestrator.

```text
Softphone -> FreeSWITCH -> Dograh Bridge -> FastAPI Voice Orchestrator
                                           -> Provider Interfaces
                                           -> Context / Memory / Tools
                                           -> Persistence / Events
```

The foundation keeps future SIP trunking isolated behind FreeSWITCH/telephony adapters. Replacing local softphones with real trunks should not require changes in conversation business logic.

## Boundaries

- FreeSWITCH: SIP registration, extension routing, local recording, future trunk placeholders.
- Dograh bridge: session routing only.
- Voice Orchestrator: session lifecycle, call lifecycle, provider selection, memory/context integration points.
- Providers: abstract contracts for STT, LLM, and TTS.
- Database: durable tenant, call, customer, transcript, memory, campaign, audit, API key, and recording data.
- Redis: session state, conversation cache, rate limiting, temporary events, distributed locks, and future queues.

## Language

The default language is `bn-BD`, with `en-US` as secondary. APIs and database columns are UTF-8 safe and do not assume English-only text.
