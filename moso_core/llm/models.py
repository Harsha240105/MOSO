from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMConfig:
    model_path: str
    n_ctx: int = 2048
    n_gpu_layers: int = 0
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    verbose: bool = False
    server_port: int = 8081
    server_host: str = "127.0.0.1"
    server_binary: str = ""


@dataclass
class LLMRequest:
    prompt: str
    system_prompt: str = ""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stream: bool = False


@dataclass
class LLMResponse:
    text: str
    tokens_generated: int = 0
    total_tokens: int = 0
    elapsed_ms: float = 0.0
    success: bool = True
    error: str = ""
