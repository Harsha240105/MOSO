from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "opus"
    PCM16 = "pcm16"


class SpeakerAuthLevel(str, Enum):
    OWNER = "owner"
    GUEST = "guest"
    BLOCKED = "blocked"


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "int16"
    block_size: int = 1024
    device: Optional[int] = None
    silence_threshold: float = 0.01
    silence_duration_ms: int = 500
    wake_word_timeout_ms: int = 3000


@dataclass
class SpeakerProfile:
    name: str = "owner"
    embedding: list[float] = field(default_factory=list)
    enrollment_samples: int = 0
    threshold: float = 0.95
    auth_level: SpeakerAuthLevel = SpeakerAuthLevel.OWNER


@dataclass
class VerificationResult:
    verified: bool
    confidence: float = 0.0
    auth_level: SpeakerAuthLevel = SpeakerAuthLevel.BLOCKED
    profile: Optional[SpeakerProfile] = None


@dataclass
class STTResult:
    text: str = ""
    language: str = "en"
    confidence: float = 0.0
    segments: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class TTSResult:
    audio_bytes: bytes = field(default_factory=bytes)
    sample_rate: int = 22050
    duration_ms: float = 0.0
    format: AudioFormat = AudioFormat.WAV


@dataclass
class VoiceSession:
    active: bool = False
    owner_verified: bool = False
    auth_level: SpeakerAuthLevel = SpeakerAuthLevel.BLOCKED
    utterances: int = 0
    session_start_ms: float = 0.0
    last_verification_ms: float = 0.0


@dataclass
class VoicePipelineResult:
    text: str = ""
    audio_response: Optional[TTSResult] = None
    verification: Optional[VerificationResult] = None
    stt_result: Optional[STTResult] = None
    error: Optional[str] = None
    session: Optional[VoiceSession] = None
