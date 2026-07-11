from app.config.settings import Settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.claude import ClaudeLLMProvider
from app.providers.llm.gpt import GPTLLMProvider
from app.providers.llm.groq import GroqLLMProvider
from app.providers.mock import MockLLMProvider, MockSTTProvider, MockTTSProvider
from app.providers.stt.base import SpeechToTextProvider
from app.providers.stt.groq_http import GroqWhisperSTTProvider
from app.providers.tts.base import TextToSpeechProvider
from app.providers.tts.cartesia import CartesiaTTSProvider
from app.providers.tts.openai import OpenAITTSProvider


class ProviderRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def configured(self) -> dict[str, str]:
        return {
            "stt": self.settings.default_stt_provider,
            "llm": self.settings.default_llm_provider,
            "tts": self.settings.default_tts_provider,
        }

    def available(self) -> dict[str, list[str]]:
        return {
            "stt": ["faster_whisper", "whisper_api", "whisper", "deepgram", "groq", "assemblyai"],
            "llm": ["claude", "gpt", "groq", "gemini", "deepseek", "openrouter", "local_vllm"],
            "tts": ["elevenlabs", "cartesia", "openai", "kokoro", "omnivoice", "piper"],
        }

    def stt(self) -> SpeechToTextProvider:
        if self.settings.default_stt_provider == "groq":
            return GroqWhisperSTTProvider(self.settings)
        return MockSTTProvider()

    def llm(self) -> LLMProvider:
        if self.settings.default_llm_provider == "claude":
            return ClaudeLLMProvider(self.settings)
        if self.settings.default_llm_provider in {"gpt", "openai"}:
            return GPTLLMProvider(self.settings)
        if self.settings.default_llm_provider == "groq":
            return GroqLLMProvider(self.settings)
        return MockLLMProvider()

    def tts(self) -> TextToSpeechProvider:
        if self.settings.default_tts_provider == "cartesia":
            return CartesiaTTSProvider(self.settings)
        if self.settings.default_tts_provider == "openai":
            return OpenAITTSProvider(self.settings)
        return MockTTSProvider()
