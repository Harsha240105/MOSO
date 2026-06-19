import logging
from enum import Enum
from typing import Iterator, Optional, Type, Union

from typing import TYPE_CHECKING

from moso_core.inference.base import InferenceConfig, ModelBackend
from moso_core.inference.llama_cpp.backend import LlamaCPPBackend
from moso_core.pipelines.base import Pipeline, PipelineResult
from moso_core.pipelines.text.pipeline import TextPipeline
from moso_core.safety.guardrails import OutputGuard, PromptGuard

if TYPE_CHECKING:
    from moso_core.voice.pipeline import VoicePipeline

logger = logging.getLogger(__name__)

BACKEND_REGISTRY: dict[str, Type[ModelBackend]] = {
    "llama": LlamaCPPBackend,
}

try:
    from moso_core.inference.onnx_runtime.backend import OnnxRuntimeBackend
    BACKEND_REGISTRY["onnx"] = OnnxRuntimeBackend
except ImportError:
    pass


def register_backend(name: str, backend_cls: Type[ModelBackend]) -> None:
    BACKEND_REGISTRY[name] = backend_cls


class Modality(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    MULTIMODAL = "multimodal"
    REASONING = "reasoning"


class Orchestrator:
    def __init__(
        self,
        config: InferenceConfig,
        system_prompt: Optional[str] = None,
        enable_safety: bool = True,
        backend: Union[str, Type[ModelBackend], ModelBackend, None] = None,
    ):
        self._config = config
        self._backend: Optional[ModelBackend] = None
        self._backend_source = backend
        self._pipelines: dict[Modality, Pipeline] = {}
        self._prompt_guard = PromptGuard() if enable_safety else None
        self._output_guard = OutputGuard() if enable_safety else None

        self._text_pipeline = TextPipeline(
            backend=self._get_or_create_backend(),
            system_prompt=system_prompt or "You are M0S0, a privacy-first, local-first adaptive AI assistant.",
        )
        self._pipelines[Modality.TEXT] = self._text_pipeline

        self._voice_pipeline = None

    def process(self, prompt: str, modality: Modality = Modality.TEXT, **kwargs) -> PipelineResult:
        if self._prompt_guard:
            guard_result = self._prompt_guard.check(prompt)
            if not guard_result.allowed:
                logger.warning("Prompt blocked: %s", guard_result.reason)
                return PipelineResult(
                    text=f"I cannot process that request. {guard_result.reason}",
                    generation=None,
                )

        pipeline = self._resolve_pipeline(modality)
        result = pipeline.run(prompt, **kwargs)

        if self._output_guard:
            result = self._output_guard.sanitize(result)

        return result

    def process_stream(
        self, prompt: str, modality: Modality = Modality.TEXT, **kwargs
    ) -> Iterator[str]:
        if self._prompt_guard:
            guard_result = self._prompt_guard.check(prompt)
            if not guard_result.allowed:
                yield f"I cannot process that request. {guard_result.reason}"
                return

        pipeline = self._resolve_pipeline(modality)
        yield from pipeline.run_stream(prompt, **kwargs)

    def enable_voice(
        self,
        stt_model=None,
        tts_model=None,
        speaker_verifier=None,
        audio_config=None,
    ) -> None:
        from moso_core.voice.pipeline import VoicePipeline
        from moso_core.voice.input import AudioStream
        from moso_core.voice.stt import WhisperSTT
        from moso_core.voice.tts import PiperTTS
        from moso_core.voice.speaker import SpeakerVerifier
        from moso_core.voice.models import AudioConfig

        self._voice_pipeline = VoicePipeline(
            backend=self._get_or_create_backend(),
            audio_config=audio_config or AudioConfig(),
            stt_model=stt_model or WhisperSTT(),
            tts_model=tts_model or PiperTTS(),
            speaker_verifier=speaker_verifier or SpeakerVerifier(),
            system_prompt=self._text_pipeline._system_prompt,
        )
        self._pipelines[Modality.VOICE] = self._voice_pipeline
        logger.info("Voice pipeline enabled")

    def process_voice(self, audio, sample_rate: int = 16000):
        if self._voice_pipeline is None:
            raise RuntimeError(
                "Voice pipeline not enabled. Call enable_voice() first."
            )
        return self._voice_pipeline.process_voice(audio, sample_rate)

    def listen_and_respond(self, audio_stream=None):
        if self._voice_pipeline is None:
            raise RuntimeError(
                "Voice pipeline not enabled. Call enable_voice() first."
            )
        return self._voice_pipeline.listen_and_respond(audio_stream)

    @property
    def voice_pipeline(self):
        return self._voice_pipeline

    def reset_conversation(self, modality: Modality = Modality.TEXT) -> None:
        pipeline = self._pipelines.get(modality)
        if pipeline:
            pipeline.reset()

    def load(self) -> None:
        self._get_or_create_backend().load()

    def unload(self) -> None:
        if self._backend is not None:
            self._backend.unload()

    @property
    def backend(self) -> ModelBackend:
        return self._get_or_create_backend()

    @property
    def text_pipeline(self) -> TextPipeline:
        return self._text_pipeline

    def _resolve_pipeline(self, modality: Modality) -> Pipeline:
        if modality not in self._pipelines:
            supported = list(self._pipelines.keys())
            raise ValueError(
                f"Unsupported modality '{modality.value}'. "
                f"Supported: {[m.value for m in supported]}"
            )
        return self._pipelines[modality]

    def _get_or_create_backend(self) -> ModelBackend:
        if self._backend is not None:
            return self._backend

        if isinstance(self._backend_source, ModelBackend):
            self._backend = self._backend_source
        elif isinstance(self._backend_source, str):
            cls = BACKEND_REGISTRY.get(self._backend_source)
            if cls is None:
                raise ValueError(
                    f"Unknown backend '{self._backend_source}'. "
                    f"Available: {list(BACKEND_REGISTRY.keys())}"
                )
            self._backend = cls(self._config)
        elif isinstance(self._backend_source, type) and issubclass(self._backend_source, ModelBackend):
            self._backend = self._backend_source(self._config)
        else:
            self._backend = LlamaCPPBackend(self._config)

        return self._backend

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *args):
        self.unload()
