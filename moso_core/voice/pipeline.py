import logging
import time
from typing import Iterator, Optional

import numpy as np

from moso_core.inference.base import ModelBackend
from moso_core.pipelines.base import Pipeline, PipelineResult
from moso_core.voice.input import AudioStream, VAD, WakeWordDetector
from moso_core.voice.models import (
    AudioConfig,
    VoicePipelineResult,
    VoiceSession,
)
from moso_core.voice.speaker import SpeakerVerifier, ContinuousAuth
from moso_core.voice.stt import WhisperSTT
from moso_core.voice.tts import PiperTTS

logger = logging.getLogger(__name__)


class VoicePipeline(Pipeline):
    def __init__(
        self,
        backend: ModelBackend,
        audio_config: Optional[AudioConfig] = None,
        stt_model: Optional[WhisperSTT] = None,
        tts_model: Optional[PiperTTS] = None,
        speaker_verifier: Optional[SpeakerVerifier] = None,
        system_prompt: Optional[str] = None,
    ):
        self._backend = backend
        self._audio_config = audio_config or AudioConfig()
        self._stt = stt_model or WhisperSTT()
        self._tts = tts_model or PiperTTS()
        self._verifier = speaker_verifier or SpeakerVerifier()
        self._vad = VAD(self._audio_config)
        self._wake_word = WakeWordDetector(self._audio_config)
        self._auth = ContinuousAuth(self._verifier)

        self._system_prompt = system_prompt or (
            "You are M0S0, a privacy-first voice AI assistant. "
            "Respond conversationally and concisely for spoken output. "
            "Keep responses brief and natural."
        )
        self._messages: list[dict] = [
            {"role": "system", "content": self._system_prompt}
        ]
        self._max_history = 20

    def run(
        self, prompt: str, audio_input: Optional[np.ndarray] = None, **kwargs
    ) -> PipelineResult:
        if audio_input is not None:
            verification = self._verifier.verify(audio_input)
            auth_result = self._auth.check_session(audio_input)

            if not auth_result.verified:
                logger.info("Speaker not verified, limited mode")
                prompt = f"[Guest mode] {prompt}"

        self._messages.append({"role": "user", "content": prompt})
        result = self._backend.chat(self._messages, **kwargs)
        self._messages.append({"role": "assistant", "content": result.text})
        self._trim_history()

        return PipelineResult(text=result.text, generation=result, messages=list(self._messages))

    def run_stream(
        self, prompt: str, audio_input: Optional[np.ndarray] = None, **kwargs
    ) -> Iterator[str]:
        if audio_input is not None:
            auth_result = self._auth.check_session(audio_input)
            if not auth_result.verified:
                prompt = f"[Guest mode] {prompt}"

        self._messages.append({"role": "user", "content": prompt})
        collected: list[str] = []
        for chunk in self._backend.chat_stream(self._messages, **kwargs):
            collected.append(chunk)
            yield chunk

        full_reply = "".join(collected)
        self._messages.append({"role": "assistant", "content": full_reply})
        self._trim_history()

    def process_voice(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
    ) -> VoicePipelineResult:
        session = self._auth.session or self._auth.start_session()

        verification = self._auth.check_session(audio, sample_rate)
        if not verification.verified:
            return VoicePipelineResult(
                text="",
                verification=verification,
                session=session,
                error="Speaker not recognized",
            )

        stt_result = self._stt.transcribe(audio, sample_rate)
        if not stt_result.text.strip():
            return VoicePipelineResult(
                text="",
                verification=verification,
                stt_result=stt_result,
                session=session,
                error="No speech detected",
            )

        pipeline_result = self.run(
            prompt=stt_result.text,
            audio_input=audio,
        )

        tts_result = self._tts.synthesize(pipeline_result.text)

        session.utterances += 1

        return VoicePipelineResult(
            text=pipeline_result.text,
            audio_response=tts_result,
            verification=verification,
            stt_result=stt_result,
            session=session,
        )

    def process_voice_stream(
        self,
        audio_chunks,
        sample_rate: int = 16000,
    ):
        for audio_chunk in audio_chunks:
            yield self.process_voice(audio_chunk, sample_rate)

    def listen_and_respond(
        self, audio_stream: AudioStream
    ) -> Optional[VoicePipelineResult]:
        if not audio_stream.is_running():
            audio_stream.start()

        audio = audio_stream.read_audio(timeout=5.0)
        if audio is None:
            return None

        return self.process_voice(audio, audio_stream.sample_rate)

    def reset(self) -> None:
        self._messages = [{"role": "system", "content": self._system_prompt}]
        self._auth.end_session()
        logger.info("Voice pipeline reset")

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt
        if self._messages and self._messages[0]["role"] == "system":
            self._messages[0]["content"] = prompt

    @property
    def history(self) -> list[dict]:
        return list(self._messages)

    @property
    def session(self) -> Optional[VoiceSession]:
        return self._auth.session

    @property
    def is_authenticated(self) -> bool:
        return self._auth.is_authenticated

    def _trim_history(self) -> None:
        if len(self._messages) > self._max_history * 2 + 1:
            keep = [self._messages[0]]
            keep.extend(self._messages[-(self._max_history * 2) :])
            self._messages = keep
