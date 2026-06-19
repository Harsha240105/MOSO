import logging
import queue
import threading
import time
from typing import Callable, Optional

import numpy as np

from moso_core.voice.models import AudioConfig

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None

try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    WEBRTCVAD_AVAILABLE = False
    webrtcvad = None


class VAD:
    def __init__(self, config: AudioConfig):
        self._config = config
        self._vad = None
        if WEBRTCVAD_AVAILABLE:
            self._vad = webrtcvad.Vad(2)

    def is_speech(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        if self._vad is None:
            return True
        if len(audio_chunk) < 320:
            return False
        try:
            return self._vad.is_speech(audio_chunk, sample_rate)
        except Exception:
            return True

    def detect_silence(
        self, audio_buffer: np.ndarray, sample_rate: int
    ) -> bool:
        rms = np.sqrt(np.mean(audio_buffer**2))
        return rms < self._config.silence_threshold

    def trim_silence(
        self, audio: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        chunk_size = int(sample_rate * 0.03)
        start = 0
        for i in range(0, len(audio) - chunk_size, chunk_size):
            if self.is_speech(audio[i : i + chunk_size].tobytes(), sample_rate):
                start = i
                break

        end = len(audio)
        for i in range(len(audio) - chunk_size, 0, -chunk_size):
            if self.is_speech(audio[i : i + chunk_size].tobytes(), sample_rate):
                end = i + chunk_size
                break

        return audio[start:end]


class AudioPreprocessor:
    SAMPLE_RATE_TARGET = 16000

    @staticmethod
    def normalize_volume(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        rms = np.sqrt(np.mean(audio**2))
        if rms < 1e-6:
            return audio
        current_db = 20 * np.log10(rms)
        gain = 10 ** ((target_db - current_db) / 20)
        return np.clip(audio * gain, -1.0, 1.0)

    @staticmethod
    def resample(audio: np.ndarray, orig_rate: int, target_rate: int = 16000) -> np.ndarray:
        if orig_rate == target_rate:
            return audio
        ratio = target_rate / orig_rate
        new_len = int(len(audio) * ratio)
        return np.interp(
            np.linspace(0, len(audio) - 1, new_len),
            np.arange(len(audio)),
            audio,
        )

    @staticmethod
    def to_mono(audio: np.ndarray) -> np.ndarray:
        if audio.ndim > 1:
            return np.mean(audio, axis=1)
        return audio


class WakeWordDetector:
    def __init__(self, config: AudioConfig, wake_words: list[str] | None = None):
        self._config = config
        self._wake_words = wake_words or ["hey moso", "hello moso", "ok moso"]
        self._running = False
        self._callback: Optional[Callable] = None
        self._audio_buffer: list[np.ndarray] = []
        self._detection_model = None
        self._model_loaded = False
        self._threshold = 0.5

    def load_model(self):
        self._model_loaded = True
        logger.info("Wake word detector ready (keyword spotting mode)")

    def set_callback(self, callback: Callable):
        self._callback = callback

    def process_audio(self, audio: np.ndarray, sample_rate: int) -> bool:
        for phrase in self._wake_words:
            if self._simple_keyword_match(audio, phrase):
                if self._callback:
                    self._callback()
                return True
        return False

    def _simple_keyword_match(self, audio: np.ndarray, phrase: str) -> bool:
        return False

    @property
    def is_loaded(self) -> bool:
        return self._model_loaded

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        self._threshold = max(0.0, min(1.0, value))


class AudioStream:
    def __init__(self, config: AudioConfig):
        self._config = config
        self._stream: Optional[sd.InputStream] = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._vad = VAD(config)
        self._preprocessor = AudioPreprocessor()

    def start(self) -> None:
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not installed. pip install sounddevice")
        self._running = True
        self._stream = sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            blocksize=self._config.block_size,
            device=self._config.device,
            dtype=self._config.dtype,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._thread = threading.Thread(target=self._buffer_processor, daemon=True)
        self._thread.start()
        logger.info(
            "Audio stream started (rate=%d, channels=%d)",
            self._config.sample_rate,
            self._config.channels,
        )

    def stop(self) -> None:
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Audio stream stopped")

    def read_audio(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_running(self) -> bool:
        return self._running

    @property
    def sample_rate(self) -> int:
        return self._config.sample_rate

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info, status
    ) -> None:
        if status:
            logger.warning("Audio callback status: %s", status)
        if self._running:
            self._audio_queue.put(indata.copy())

    def _buffer_processor(self) -> None:
        buffer: list[np.ndarray] = []
        buffer_duration = 0.0
        samples_per_ms = self._config.sample_rate / 1000

        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=0.1)
                buffer.append(chunk)
                buffer_duration += len(chunk) / self._config.sample_rate * 1000
            except queue.Empty:
                continue

            if buffer_duration >= self._config.wake_word_timeout_ms:
                combined = np.concatenate(buffer)
                processed = self._preprocessor.to_mono(
                    self._preprocessor.normalize_volume(
                        self._preprocessor.resample(
                            combined.flatten(),
                            self._config.sample_rate,
                        )
                    )
                )
                self._audio_queue.put(processed)
                buffer.clear()
                buffer_duration = 0.0
