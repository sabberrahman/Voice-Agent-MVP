# Environment Variables

Copy `.env.example` to `.env` for local customization. This scaffold includes a local `.env` so `docker compose up` works immediately.

Core variables:

- `APP_PORT`: FastAPI host port.
- `POSTGRES_*`: PostgreSQL connection settings.
- `REDIS_*`: Redis connection settings.
- `FREESWITCH_SIP_PORT`: SIP registration port.
- `FREESWITCH_EXTENSION_1001_PASSWORD`: SIP password for extension `1001`.
- `FREESWITCH_EXTENSION_1002_PASSWORD`: SIP password for extension `1002`.
- `DEFAULT_STT_PROVIDER`: configured STT provider key.
- `DEFAULT_LLM_PROVIDER`: configured LLM provider key.
- `DEFAULT_TTS_PROVIDER`: configured TTS provider key.
- `GROQ_API_KEY`: Groq API key for Whisper transcription and Groq LLM chat.
- `GROQ_STT_MODEL`: Groq Whisper transcription model.
- `GROQ_LLM_MODEL`: Groq chat model when `DEFAULT_LLM_PROVIDER=groq`.
- `ANTHROPIC_API_KEY`: Claude Messages API key.
- `CARTESIA_API_KEY`: Cartesia TTS key.
- `CARTESIA_VOICE_ID`: Cartesia voice identifier.
- `CARTESIA_VOICE_RUBUL_MALE`: optional named Cartesia voice ID for Rubul male.
- `CARTESIA_VOICE_POOJA`: optional named Cartesia voice ID for Pooja.
- `OPENAI_API_KEY`: OpenAI alternative LLM/TTS key.
- `PROVIDER_RETRY_ATTEMPTS`: provider retry count.
- `LLM_MAX_TOKENS`: maximum LLM response tokens.
- `SUPPORTED_LANGUAGES`: comma-separated language tags.

Secrets are environment-driven so they can later move to a proper secret manager.
