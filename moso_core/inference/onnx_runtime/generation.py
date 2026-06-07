import logging
import time
from typing import Iterator, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ONNXGenerator:
    def __init__(
        self,
        session,
        tokenizer,
        eos_token_id: Optional[int] = None,
        pad_token_id: Optional[int] = None,
    ):
        self.session = session
        self.tokenizer = tokenizer
        self.eos_token_id = eos_token_id or tokenizer.eos_token_id
        self.pad_token_id = pad_token_id or tokenizer.pad_token_id or 0

        self._input_names = [inp.name for inp in session.get_inputs()]
        self._output_names = [out.name for out in session.get_outputs()]

        self._has_past = "past_key_values" in self._input_names
        self._has_present = "present_key_values" in self._output_names

        logger.debug(
            "ONNX model inputs=%s outputs=%s has_past=%s",
            self._input_names,
            self._output_names,
            self._has_past,
        )

    def generate_loop(
        self,
        input_ids: np.ndarray,
        attention_mask: np.ndarray,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int,
    ) -> Iterator[np.ndarray]:
        """
        Autoregressive generation loop.

        Args:
            input_ids: [1, seq_len] int64 array of input token IDs.
            attention_mask: [1, seq_len] int64 array.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (>0).
            top_p: Nucleus sampling threshold.
            top_k: Top-k sampling.

        Yields:
            Each newly generated token ID as a scalar ndarray.
        """
        current_ids = input_ids
        current_mask = attention_mask
        past = None

        for _ in range(max_tokens):
            inputs = self._build_inputs(current_ids, current_mask, past)

            outputs = self.session.run(None, inputs)
            logits = outputs[0]

            if self._has_present:
                past = outputs[1:]

            next_token_logits = logits[0, -1, :]

            next_token = self._sample(next_token_logits, temperature, top_p, top_k)
            yield next_token

            if next_token.item() == self.eos_token_id:
                break

            current_ids = next_token.reshape(1, 1)

            if self._has_past:
                current_mask = np.ones((1, current_mask.shape[1] + 1), dtype=np.int64)
            else:
                current_ids = np.concatenate(
                    [current_ids, next_token.reshape(1, 1)], axis=1
                )
                current_mask = np.concatenate(
                    [current_mask, np.ones((1, 1), dtype=np.int64)], axis=1
                )

    def _build_inputs(
        self, input_ids: np.ndarray, attention_mask: np.ndarray, past: Optional[list]
    ) -> dict:
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        if "position_ids" in self._input_names:
            seq_len = input_ids.shape[1]
            if past is not None and self._has_past:
                past_len = attention_mask.shape[1] - seq_len
                position_ids = np.arange(
                    past_len, past_len + seq_len, dtype=np.int64
                ).reshape(1, -1)
            else:
                position_ids = np.arange(seq_len, dtype=np.int64).reshape(1, -1)
            inputs["position_ids"] = position_ids

        if self._has_past:
            if past is not None:
                for i, p in enumerate(past):
                    inputs[f"past_key_values.{i}.key"] = p[0]
                    inputs[f"past_key_values.{i}.value"] = p[1]
            else:
                for i in range(self._num_past_layers()):
                    inputs[f"past_key_values.{i}.key"] = np.empty(
                        (1, 0, 0, 0), dtype=np.float32
                    )
                    inputs[f"past_key_values.{i}.value"] = np.empty(
                        (1, 0, 0, 0), dtype=np.float32
                    )

        return inputs

    def _num_past_layers(self) -> int:
        past_inputs = [n for n in self._input_names if "past_key_values" in n]
        keys = [n for n in past_inputs if n.endswith(".key")]
        return len(keys)

    @staticmethod
    def _sample(
        logits: np.ndarray, temperature: float, top_p: float, top_k: int
    ) -> np.ndarray:
        if temperature < 1e-6:
            return np.argmax(logits, axis=-1, keepdims=True)

        logits = logits / temperature

        if top_k > 0:
            indices_to_remove = np.argpartition(-logits, top_k)[top_k:]
            logits[indices_to_remove] = float("-inf")

        if top_p < 1.0:
            sorted_indices = np.argsort(-logits)
            sorted_logits = logits[sorted_indices]
            cumulative_probs = np.cumsum(
                np.exp(sorted_logits - np.max(sorted_logits))
                / np.sum(np.exp(sorted_logits - np.max(sorted_logits)))
            )
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].copy()
            sorted_indices_to_remove[0] = False
            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            logits[indices_to_remove] = float("-inf")

        probs = np.exp(logits - np.max(logits))
        probs = probs / np.sum(probs)
        return np.array(
            [np.random.choice(len(probs), p=probs)], dtype=np.int64
        ).reshape(1, 1)
