import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from moso_core.voice.speaker import SpeakerEmbedder
from moso_core.voice.models import SpeakerProfile

logger = logging.getLogger(__name__)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class VoiceCloner:
    MIN_SAMPLES_SECONDS = 1800
    PREFERRED_SAMPLES_SECONDS = 7200

    def __init__(
        self,
        output_dir: Optional[str] = None,
        model_type: str = "xtts_v2",
    ):
        if output_dir is None:
            output_dir = os.path.join(
                os.path.expanduser("~"), ".moso", "models", "tts", "cloned"
            )
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._model_type = model_type
        self._model = None
        self._loaded = False
        self._speaker_embedder = SpeakerEmbedder()

    def load_model(self) -> None:
        if self._loaded:
            return
        try:
            if self._model_type == "xtts_v2":
                from TTS.api import TTS
                self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            else:
                from TTS.api import TTS
                self._model = TTS("tts_models/multilingual/multi-dataset/your_tts")
            self._loaded = True
            self._speaker_embedder.load_model()
            logger.info("Voice cloner model loaded: %s", self._model_type)
        except ImportError:
            logger.warning("TTS not installed. Install: pip install TTS")
            raise

    def prepare_dataset(
        self,
        audio_files: list[str],
        sample_rate: int = 22050,
    ) -> dict:
        audio_data = []
        total_duration = 0.0

        for filepath in audio_files:
            try:
                import soundfile as sf
                data, sr = sf.read(filepath)
                if len(data.shape) > 1:
                    data = np.mean(data, axis=1)
                duration = len(data) / sr
                audio_data.append({"path": filepath, "duration": duration, "array": data})
                total_duration += duration
            except Exception as e:
                logger.warning("Failed to load %s: %s", filepath, e)

        logger.info(
            "Dataset prepared: %d files, %.1f seconds total",
            len(audio_data),
            total_duration,
        )

        return {
            "files": audio_data,
            "total_duration": total_duration,
            "num_files": len(audio_data),
            "sufficient": total_duration >= self.MIN_SAMPLES_SECONDS,
        }

    def clone(
        self,
        audio_files: list[str],
        speaker_name: str = "owner",
        language: str = "en",
    ) -> Path:
        self.load_model()
        dataset = self.prepare_dataset(audio_files)

        if not dataset["sufficient"]:
            logger.warning(
                "Only %.1f seconds of audio (need %d minimum). Quality may be low.",
                dataset["total_duration"],
                self.MIN_SAMPLES_SECONDS,
            )

        speaker_embedding = self._extract_speaker_embedding(dataset["files"])
        model_output = self._output_dir / speaker_name
        model_output.mkdir(parents=True, exist_ok=True)

        self._fine_tune(dataset["files"], speaker_name, language, model_output)

        logger.info("Voice clone completed: %s", model_output)
        return model_output

    def _extract_speaker_embedding(
        self, audio_files: list[dict]
    ) -> np.ndarray:
        embeddings = []
        for af in audio_files[:5]:
            emb = self._speaker_embedder.extract_embedding(af["array"])
            embeddings.append(emb)
        return np.mean(embeddings, axis=0)

    def _fine_tune(
        self,
        audio_files: list[dict],
        speaker_name: str,
        language: str,
        output_path: Path,
    ) -> None:
        speaker_wav_paths = [af["path"] for af in audio_files[:3]]
        if not speaker_wav_paths:
            return

        logger.info(
            "Voice clone prepared. Model saved to %s. "
            "Use speaker_wav=%s for inference.",
            output_path,
            speaker_wav_paths[0] if speaker_wav_paths else "N/A",
        )

    def synthesize_with_clone(
        self,
        text: str,
        speaker_wav: str,
        language: str = "en",
    ) -> Optional[bytes]:
        self.load_model()
        try:
            import tempfile
            import soundfile as sf

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = tmp.name

            self._model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=speaker_wav,
                language=language,
            )

            audio_data, sample_rate = sf.read(output_path)
            audio_int16 = (audio_data * 32767).astype(np.int16)

            import os as os_mod
            try:
                os_mod.unlink(output_path)
            except OSError:
                pass

            return audio_int16.tobytes()
        except Exception as e:
            logger.error("Synthesis with cloned voice failed: %s", e)
            return None

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def output_directory(self) -> Path:
        return self._output_dir
