# AI Voice Pipeline

Prompt 2 adds the provider-agnostic voice pipeline without regenerating Docker Compose or FreeSWITCH infrastructure.

## Flow

```text
FreeSWITCH -> Dograh -> Voice Orchestrator
  -> STT provider
  -> Context Builder
  -> Conversation Manager
  -> LLM provider
  -> Tool interfaces
  -> Memory
  -> TTS provider
  -> Dograh -> Caller
```

Dograh forwards audio and events only. It does not call STT, LLM, or TTS providers.

## Default Providers

- STT: Groq Whisper API
- LLM: Claude Messages API by default, or Groq chat completions when `DEFAULT_LLM_PROVIDER=groq`
- TTS: Cartesia bytes TTS

Groq and OpenAI LLM alternatives and OpenAI TTS are implemented behind the same interfaces. Other providers have adapter placeholders and can be filled without changing business logic.

## Required Keys

Set these in `.env` for the default cloud pipeline:

```text
GROQ_API_KEY=
GROQ_LLM_MODEL=llama-3.3-70b-versatile
ANTHROPIC_API_KEY=
CARTESIA_API_KEY=
CARTESIA_VOICE_ID=
```

Provider switching:

```text
DEFAULT_STT_PROVIDER=groq
DEFAULT_LLM_PROVIDER=groq
DEFAULT_TTS_PROVIDER=cartesia
```

## API

Start a voice session:

```http
POST /voice/start
```

Send an audio turn:

```http
POST /voice/audio
Content-Type: multipart/form-data

call_id=<uuid>
session_id=<uuid>
language=bn-BD
audio=@turn.wav
```

The response streams synthesized audio. Metadata is returned in headers:

- `x-call-id`
- `x-session-id`
- `x-transcript`
- `x-response-text`
- `x-latencies-ms`

End a voice session and generate a summary:

```http
POST /voice/end
```

Read data:

- `GET /calls`
- `GET /calls/{id}`
- `GET /transcripts/{call_id}`
- `GET /summary/{call_id}`
- `GET /metrics`
- `GET /dashboard`

## Persistence

The pipeline stores calls, call events, customer and assistant transcripts, latency metadata, provider usage events, and final summaries in PostgreSQL. Active session memory is cached in Redis.

## Streaming

The provider contracts expose streaming methods. The current request/response audio endpoint streams synthesized audio back to Dograh and is ready to evolve into lower-latency chunked STT/LLM/TTS and barge-in handling.
