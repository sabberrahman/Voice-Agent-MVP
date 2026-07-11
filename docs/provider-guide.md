# Provider Guide

Provider switching remains configuration-driven.

Defaults:

- STT: `groq`
- LLM: `claude`
- TTS: `cartesia`

Alternatives:

- LLM: `gpt`
- TTS: `openai`

Future adapters:

- STT: Deepgram, AssemblyAI, Faster Whisper
- LLM: Gemini, DeepSeek, OpenRouter, local vLLM
- TTS: ElevenLabs, OmniVoice, Piper

Business logic depends on interfaces in `services/api/app/providers/*/base.py`.
