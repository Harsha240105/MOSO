import logging
import time
from pathlib import Path
from typing import Iterator, Optional

import numpy as np
import onnxruntime
from transformers import AutoTokenizer

from moso_core.inference.base import GenerationResult, GenerationStats, InferenceConfig, ModelBackend
from moso_core.inference.onnx_runtime.generation import ONNXGenerator

logger = logging.getLogger(__name__)

EXECUTION_PROVIDERS = [
    ("CUDAExecutionProvider", {"cudnn_conv_algo_search": "DEFAULT"}),
    "CoreMLExecutionProvider",
    "DmlExecutionProvider",
    "CPUExecutionProvider",
]


def _resolve_model_path(model_path: str) -> tuple[str, str]:
    p = Path(model_path)
    if p.is_dir():
        onnx_files = list(p.glob("*.onnx"))
        if not onnx_files:
            raise FileNotFoundError(f"No .onnx files found in {p}")
        return str(onnx_files[0]), str(p)
    if p.suffix == ".onnx":
        return str(p), str(p.parent)
    return str(p), str(p.parent)


class OnnxRuntimeBackend(ModelBackend):
    def __init__(self, config: InferenceConfig):
        super().__init__(config)
        self._session: Optional[onnxruntime.InferenceSession] = None
        self._tokenizer = None
        self._generator: Optional[ONNXGenerator] = None
        self._model_dir: Optional[str] = None

    def load(self) -> None:
        if self._session is not None:
            logger.warning("Session already loaded, unloading first")
            self.unload()

        model_path_str, model_dir = _resolve_model_path(self.config.model_path)
        self._model_dir = model_dir

        providers = self._available_providers()
        logger.info(
            "Loading ONNX model %s (providers=%s, ctx=%d)",
            model_path_str,
            providers,
            self.config.n_ctx,
        )
        start = time.perf_counter()

        so = onnxruntime.SessionOptions()
        so.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        so.intra_op_num_threads = self.config.n_threads or 0

        self._session = onnxruntime.InferenceSession(
            model_path_str, sess_options=so, providers=providers
        )

        logger.info(
            "Loading tokenizer from %s",
            model_dir,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_dir,
            trust_remote_code=True,
            model_max_length=self.config.n_ctx,
        )
        if self._tokenizer.pad_token_id is None:
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id

        self._generator = ONNXGenerator(
            session=self._session,
            tokenizer=self._tokenizer,
        )

        elapsed = time.perf_counter() - start
        logger.info("ONNX model loaded in %.2fs", elapsed)

    def generate(self, prompt: str, **kwargs) -> GenerationResult:
        self._require_loaded()
        tokens = self._tokenizer(
            prompt,
            return_tensors="np",
            truncation=True,
            max_length=self.config.n_ctx - self.config.max_tokens,
        )
        input_ids = tokens["input_ids"]
        attention_mask = tokens["attention_mask"]

        merged = {**self._sampling_params(), **kwargs}
        start_time = time.perf_counter()
        all_tokens = list(
            self._generator.generate_loop(
                input_ids, attention_mask, **merged
            )
        )
        elapsed = time.perf_counter() - start_time

        token_ids = [t.item() for t in all_tokens]
        text = self._tokenizer.decode(token_ids, skip_special_tokens=True)
        stats = GenerationStats(
            tokens_generated=len(token_ids),
            total_time_ms=round(elapsed * 1000, 2),
            tokens_per_second=round(len(token_ids) / elapsed, 2) if elapsed > 0 else 0.0,
            prompt_tokens=int(input_ids.shape[1]),
        )
        return GenerationResult(text=text, stats=stats)

    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        self._require_loaded()
        tokens = self._tokenizer(
            prompt,
            return_tensors="np",
            truncation=True,
            max_length=self.config.n_ctx - self.config.max_tokens,
        )
        input_ids = tokens["input_ids"]
        attention_mask = tokens["attention_mask"]

        merged = {**self._sampling_params(), **kwargs}
        collected_ids: list[int] = []
        for token in self._generator.generate_loop(input_ids, attention_mask, **merged):
            collected_ids.append(token.item())
            yield self._tokenizer.decode(token.item(), skip_special_tokens=True)

    def chat(self, messages: list[dict], **kwargs) -> GenerationResult:
        self._require_loaded()
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        return self.generate(prompt, **kwargs)

    def chat_stream(self, messages: list[dict], **kwargs) -> Iterator[str]:
        self._require_loaded()
        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        yield from self.generate_stream(prompt, **kwargs)

    def unload(self) -> None:
        self._session = None
        self._tokenizer = None
        self._generator = None
        logger.info("ONNX model unloaded")

    def tokenize(self, text: str) -> list[int]:
        self._require_loaded()
        return self._tokenizer.encode(text)

    def detokenize(self, tokens: list[int]) -> str:
        self._require_loaded()
        return self._tokenizer.decode(tokens, skip_special_tokens=True)

    @property
    def is_loaded(self) -> bool:
        return self._session is not None

    def _require_loaded(self) -> None:
        if self._session is None:
            raise RuntimeError("Model is not loaded. Call load() first.")

    def _sampling_params(self) -> dict:
        return {
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
        }

    @staticmethod
    def _available_providers() -> list[str]:
        available = onnxruntime.get_available_providers()
        prioritized = []
        for provider_spec in EXECUTION_PROVIDERS:
            if isinstance(provider_spec, tuple):
                name, options = provider_spec
                if name in available:
                    prioritized.append((name, options))
            elif provider_spec in available:
                prioritized.append(provider_spec)
        if not prioritized:
            prioritized.append("CPUExecutionProvider")
        return prioritized
