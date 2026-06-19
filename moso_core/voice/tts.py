import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

import numpy as np

from moso_core.voice.models import AudioFormat, TTSResult

logger = logging.getLogger(__name__)

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    sf = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class PiperTTS:
    def __init__(self, model_path: Optional[str] = None, voice: str = "en_US-lessac-medium"):
        self._model_path = model_path
        self._voice = voice
        self._loaded = False
        self._tts_pipeline = None

    def load_model(self) -> None:
        if self._loaded:
            return
        try:
            import piper
            self._loaded = True
            logger.info("Piper TTS ready (voice: %s)", self._voice)
        except ImportError:
            logger.warning(
                "Piper TTS not installed. Install: pip install piper-tts"
            )
            raise

    def synthesize(self, text: str, voice: Optional[str] = None) -> TTSResult:
        self.load_model()
        voice = voice or self._voice

        if not text.strip():
            return TTSResult()

        try:
            from piper import PiperVoice
            import wave
            import io

            model_path = self._model_path or self._find_model(voice)
            if model_path and os.path.exists(model_path):
                piper_voice = PiperVoice.load(model_path)
                wav_io = io.BytesIO()
                with wave.open(wav_io, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(22050)
                    piper_voice.synthesize(text, wf)
                audio_bytes = wav_io.getvalue()
            else:
                audio_data = self._simple_synthesize(text)
                audio_bytes = audio_data.tobytes()

            duration_ms = len(audio_bytes) / (22050 * 2) * 1000
            return TTSResult(
                audio_bytes=audio_bytes,
                sample_rate=22050,
                duration_ms=duration_ms,
                format=AudioFormat.WAV,
            )
        except Exception as e:
            logger.error("Piper TTS synthesis failed: %s", e)
            audio_data = self._simple_synthesize(text)
            return TTSResult(
                audio_bytes=audio_data.tobytes(),
                sample_rate=22050,
                duration_ms=len(audio_data) / 22050 * 1000,
            )

    def _find_model(self, voice: str) -> Optional[str]:
        search_paths = [
            os.path.join(os.path.expanduser("~"), ".moso", "models", "tts"),
            os.path.join(".", "models", "speech", "tts"),
        ]
        for base in search_paths:
            pattern = f"{voice}.onnx"
            for f in Path(base).glob(pattern):
                return str(f)
        return None

    def _simple_synthesize(self, text: str) -> np.ndarray:
        duration = max(0.5, len(text) * 0.08)
        num_samples = int(22050 * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        frequencies = [200, 300, 250]
        audio = np.zeros(num_samples)
        for i, freq in enumerate(frequencies):
            audio += 0.1 * np.sin(2 * np.pi * freq * t)
        audio = np.clip(audio, -1.0, 1.0)
        return (audio * 32767).astype(np.int16)

    @property
    def is_loaded(self) -> bool:
        return self._loaded


class CoquiTTS:
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        self._model_name = model_name
        self._model = None
        self._loaded = False

    def load_model(self) -> None:
        if self._loaded:
            return
        try:
            from TTS.api import TTS
            self._model = TTS(self._model_name)
            self._loaded = True
            logger.info("Coqui TTS loaded: %s", self._model_name)
        except ImportError:
            logger.warning("Coqui TTS not installed. Install: pip install TTS")
            raise

    def synthesize(
        self,
        text: str,
        speaker_wav: Optional[str] = None,
        language: str = "en",
    ) -> TTSResult:
        self.load_model()
        if not text.strip():
            return TTSResult()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        try:
            self._model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=speaker_wav,
                language=language,
            )

            import soundfile as sf
            audio_data, sample_rate = sf.read(output_path)
            audio_int16 = (audio_data * 32767).astype(np.int16)
            duration_ms = len(audio_int16) / sample_rate * 1000

            return TTSResult(
                audio_bytes=audio_int16.tobytes(),
                sample_rate=sample_rate,
                duration_ms=duration_ms,
                format=AudioFormat.WAV,
            )
        except Exception as e:
            logger.error("Coqui TTS synthesis failed: %s", e)
            raise
        finally:
            try:
                os.unlink(output_path)
            except OSError:
                pass

    def synthesize_stream(
        self,
        text: str,
        speaker_wav: Optional[str] = None,
        language: str = "en",
    ):
        self.load_model()
        yield self.synthesize(text, speaker_wav, language)

    @property
    def is_loaded(self) -> bool:
        return self._loaded
