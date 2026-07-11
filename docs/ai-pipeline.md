# AI Voice Pipeline

Prompt 2 adds the provider-agnostic voice pipeline without regenerating Docker Compose or FreeSWITCH infrastructure.

## Flow

```text
FreeSWITCH -> mod_audio_stream -> Dograh WebSocket -> Voice Orchestrator WebSocket
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

Redis is the live-call buffer. The API writes session state, recent history, transcript turns, and call events into Redis while the call is active. PostgreSQL writes are deferred until the call ends, which keeps DB I/O out of the audio-response path.

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

Preferred low-latency socket:

```text
ws://localhost:8000/voice/ws
ws://localhost:8010/ws
ws://localhost:8010/freeswitch/media
```

Socket message types:

```json
{"type":"start","payload":{"direction":"inbound","from_number":"1001","to_number":"ai","language":"bn-BD"}}
{"type":"audio","payload":{"call_id":"<uuid>","session_id":"<uuid>","language":"bn-BD","audio_b64":"<base64-wav-or-frame>"}}
{"type":"event","payload":{"call_id":"<uuid>","session_id":"<uuid>","event_type":"pbx.event","payload":{}}}
{"type":"end","payload":{"call_id":"<uuid>","session_id":"<uuid>","reason":"hangup"}}
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

The pipeline stores live call state in Redis first:

- `session:{session_id}` for active memory and recent history
- `call:{call_id}` for call metadata and final summary
- `call:{call_id}:events` for live events
- `call:{call_id}:transcripts` for customer and assistant turns
- `calls:active` for active call lookup

When `/voice/end` or the WebSocket `end` message arrives, Redis buffers are flushed into PostgreSQL as call history, events, transcripts, and summary rows.

## Streaming

The provider contracts expose streaming methods. The transport is now WebSocket-ready so PBX/Dograh/API can keep one connection open and avoid repeated multipart HTTP setup. Provider-level chunked STT/LLM/TTS and barge-in can be layered on top of the same socket protocol.

## FreeSWITCH AI Agent

Extension `7000` is the AI agent route. It answers the SIP call, records locally, starts `uuid_audio_stream`, and parks the channel while Dograh and the API handle the conversation.

Outbound AI-to-human calls use:

```http
POST /admin/start-outbound-zoiper/1001
```

That asks Dograh to originate `user/1001` through FreeSWITCH ESL, then FreeSWITCH connects the answered call to extension `7000`.
