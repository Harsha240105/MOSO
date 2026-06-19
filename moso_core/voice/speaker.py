import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import numpy as np

from moso_core.voice.models import (
    SpeakerAuthLevel,
    SpeakerProfile,
    VerificationResult,
    VoiceSession,
)

logger = logging.getLogger(__name__)

try:
    from speechbrain.inference.speaker import SpeakerRecognition
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False
    SpeakerRecognition = None


class SpeakerEmbedder:
    MODEL_ID = "speechbrain/spkrec-ecapa-voxceleb"

    def __init__(self, device: str = "cpu"):
        self._device = device
        self._model = None
        self._embedding_dim = 192

    def load_model(self) -> None:
        if not SPEECHBRAIN_AVAILABLE:
            logger.warning(
                "SpeechBrain not installed. Install: pip install speechbrain"
            )
            return
        if self._model is None:
            logger.info("Loading ECAPA-TDNN speaker verification model...")
            self._model = SpeakerRecognition.from_hparams(
                source=self.MODEL_ID,
                savedir=os.path.join(
                    os.path.expanduser("~"), ".moso", "models", "speaker"
                ),
                run_opts={"device": self._device},
            )
            logger.info("Speaker verification model loaded")

    def extract_embedding(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        if self._model is None:
            return np.random.randn(self._embedding_dim).astype(np.float32)
        import torch
        waveform = torch.from_numpy(audio).float()
        embedding = self._model.encode_batch(waveform.unsqueeze(0))
        return embedding.squeeze().cpu().numpy().astype(np.float32)

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        norm1 = embedding1 / (np.linalg.norm(embedding1) + 1e-10)
        norm2 = embedding2 / (np.linalg.norm(embedding2) + 1e-10)
        similarity = float(np.dot(norm1, norm2))
        return max(0.0, min(1.0, similarity))

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim


class SpeakerStore:
    def __init__(self, store_path: Optional[str] = None):
        if store_path is None:
            store_path = os.path.join(
                os.path.expanduser("~"), ".moso", "speakers"
            )
        self._store_path = Path(store_path)
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, SpeakerProfile] = {}
        self._load_all()

    def save_profile(self, profile: SpeakerProfile) -> None:
        data = {
            "name": profile.name,
            "embedding": [float(x) for x in profile.embedding],
            "enrollment_samples": profile.enrollment_samples,
            "threshold": profile.threshold,
            "auth_level": profile.auth_level.value,
        }
        filepath = self._store_path / f"{profile.name}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        self._profiles[profile.name] = profile
        logger.info("Speaker profile saved: %s", filepath)

    def load_profile(self, name: str) -> Optional[SpeakerProfile]:
        filepath = self._store_path / f"{name}.json"
        if not filepath.exists():
            return None
        with open(filepath) as f:
            data = json.load(f)
        profile = SpeakerProfile(
            name=data["name"],
            embedding=np.array(data["embedding"], dtype=np.float32),
            enrollment_samples=data["enrollment_samples"],
            threshold=data["threshold"],
            auth_level=SpeakerAuthLevel(data["auth_level"]),
        )
        self._profiles[name] = profile
        return profile

    def delete_profile(self, name: str) -> bool:
        filepath = self._store_path / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            self._profiles.pop(name, None)
            return True
        return False

    def profile_exists(self, name: str) -> bool:
        return (self._store_path / f"{name}.json").exists()

    def list_profiles(self) -> list[str]:
        return [f.stem for f in self._store_path.glob("*.json")]

    def _load_all(self) -> None:
        for filepath in self._store_path.glob("*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                profile = SpeakerProfile(
                    name=data["name"],
                    embedding=np.array(data["embedding"], dtype=np.float32),
                    enrollment_samples=data["enrollment_samples"],
                    threshold=data["threshold"],
                    auth_level=SpeakerAuthLevel(data["auth_level"]),
                )
                self._profiles[data["name"]] = profile
            except Exception as e:
                logger.warning("Failed to load profile %s: %s", filepath, e)


class SpeakerVerifier:
    def __init__(
        self,
        embedder: Optional[SpeakerEmbedder] = None,
        store: Optional[SpeakerStore] = None,
    ):
        self._embedder = embedder or SpeakerEmbedder()
        self._store = store or SpeakerStore()

    def verify(
        self, audio: np.ndarray, sample_rate: int = 16000, profile_name: str = "owner"
    ) -> VerificationResult:
        if not self._embedder.is_loaded:
            self._embedder.load_model()

        live_embedding = self._embedder.extract_embedding(audio, sample_rate)
        profile = self._store.load_profile(profile_name)

        if profile is None:
            return VerificationResult(
                verified=False,
                confidence=0.0,
                auth_level=SpeakerAuthLevel.BLOCKED,
            )

        similarity = self._embedder.compute_similarity(live_embedding, profile.embedding)
        verified = similarity >= profile.threshold

        auth_level = (
            SpeakerAuthLevel.OWNER
            if verified
            else SpeakerAuthLevel.GUEST
        )

        return VerificationResult(
            verified=verified,
            confidence=similarity,
            auth_level=auth_level,
            profile=profile if verified else None,
        )

    def enroll(
        self,
        audio_samples: list[np.ndarray],
        sample_rate: int = 16000,
        name: str = "owner",
    ) -> SpeakerProfile:
        if not self._embedder.is_loaded:
            self._embedder.load_model()

        embeddings = []
        for sample in audio_samples:
            emb = self._embedder.extract_embedding(sample, sample_rate)
            embeddings.append(emb)

        avg_embedding = np.mean(embeddings, axis=0).astype(np.float32)
        avg_embedding /= np.linalg.norm(avg_embedding) + 1e-10

        profile = SpeakerProfile(
            name=name,
            embedding=avg_embedding.tolist(),
            enrollment_samples=len(audio_samples),
            threshold=0.95,
            auth_level=SpeakerAuthLevel.OWNER,
        )
        self._store.save_profile(profile)
        logger.info(
            "Enrolled speaker '%s' with %d samples",
            name,
            len(audio_samples),
        )
        return profile


class EnrollmentManager:
    def __init__(self, verifier: SpeakerVerifier):
        self._verifier = verifier
        self._samples: list[np.ndarray] = []
        self._required_samples = 3
        self._max_samples = 5

    def add_sample(self, audio: np.ndarray) -> int:
        self._samples.append(audio)
        return len(self._samples)

    def is_ready(self) -> bool:
        return len(self._samples) >= self._required_samples

    def remaining(self) -> int:
        return max(0, self._required_samples - len(self._samples))

    def complete(self, name: str = "owner") -> SpeakerProfile:
        if not self.is_ready():
            raise ValueError(
                f"Need {self.remaining()} more sample(s) for enrollment"
            )
        profile = self._verifier.enroll(self._samples[: self._max_samples], name=name)
        self._samples.clear()
        return profile

    def reset(self) -> None:
        self._samples.clear()

    @property
    def sample_count(self) -> int:
        return len(self._samples)


class ContinuousAuth:
    def __init__(
        self,
        verifier: SpeakerVerifier,
        re_verify_interval_ms: int = 60000,
        session_timeout_ms: int = 300000,
    ):
        self._verifier = verifier
        self._re_verify_interval_ms = re_verify_interval_ms
        self._session_timeout_ms = session_timeout_ms
        self._session: Optional[VoiceSession] = None

    def start_session(self) -> VoiceSession:
        self._session = VoiceSession(
            active=True,
            session_start_ms=time.time() * 1000,
            last_verification_ms=time.time() * 1000,
        )
        logger.info("Voice session started")
        return self._session

    def end_session(self) -> None:
        if self._session:
            self._session.active = False
            logger.info("Voice session ended")

    def check_session(self, audio: np.ndarray, sample_rate: int = 16000) -> VerificationResult:
        if self._session is None:
            self.start_session()

        current_ms = time.time() * 1000
        elapsed_since_verify = current_ms - self._session.last_verification_ms

        if elapsed_since_verify < self._re_verify_interval_ms:
            return VerificationResult(
                verified=self._session.owner_verified,
                auth_level=self._session.auth_level,
            )

        result = self._verifier.verify(audio, sample_rate)
        self._session.owner_verified = result.verified
        self._session.auth_level = result.auth_level
        self._session.last_verification_ms = current_ms

        if not result.verified:
            session_elapsed = current_ms - self._session.session_start_ms
            if session_elapsed > self._session_timeout_ms:
                self.end_session()

        return result

    @property
    def session(self) -> Optional[VoiceSession]:
        return self._session

    @property
    def is_authenticated(self) -> bool:
        return self._session is not None and self._session.owner_verified
