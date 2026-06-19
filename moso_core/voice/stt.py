import logging
import time
from typing import Optional

import numpy as np

from moso_core.voice.models import STTResult

logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None


class WhisperSTT:
    MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        if model_size not in self.MODEL_SIZES:
            raise ValueError(
                f"Model size must be one of {self.MODEL_SIZES}, got '{model_size}'"
            )
        self._model_size = model_size
        self._device = device
        self._model = None

    def load_model(self) -> None:
        if not WHISPER_AVAILABLE:
            raise RuntimeError(
                "Whisper not installed. Install: pip install openai-whisper"
            )
        if self._model is None:
            logger.info("Loading Whisper model '%s'...", self._model_size)
            start = time.perf_counter()
            self._model = whisper.load_model(self._model_size, device=self._device)
            elapsed = time.perf_counter() - start
            logger.info("Whisper model loaded in %.2fs", elapsed)

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        word_timestamps: bool = False,
    ) -> STTResult:
        if self._model is None:
            self.load_model()

        audio_float = audio.astype(np.float32)
        if np.abs(audio_float).max() > 1.0:
            audio_float = audio_float / 32768.0

        start = time.perf_counter()
        result = self._model.transcribe(
            audio_float,
            language=language,
            word_timestamps=word_timestamps,
            fp16=False,
        )
        elapsed = time.perf_counter() - start

        segments = [
            {
                "text": seg["text"].strip(),
                "start": seg["start"],
                "end": seg["end"],
                "confidence": seg.get("confidence", 0.0),
            }
            for seg in result.get("segments", [])
        ]

        return STTResult(
            text=result.get("text", "").strip(),
            language=result.get("language", "en"),
            confidence=(
                result["segments"][0]["confidence"]
                if result.get("segments")
                else 0.0
            ),
            segments=segments,
            duration_ms=elapsed * 1000,
        )

    def transcribe_stream(
        self,
        audio_generator,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ):
        if self._model is None:
            self.load_model()

        for audio_chunk in audio_generator:
            yield self.transcribe(audio_chunk, sample_rate, language)

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_size(self) -> str:
        return self._model_size
