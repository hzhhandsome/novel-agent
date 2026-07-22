from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.core.config import settings


class TokenizerLike(Protocol):
    name_or_path: str

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        ...


@dataclass(frozen=True)
class TokenCountResult:
    tokens: int
    chars: int
    counter_name: str
    is_fallback: bool


class TokenCounter:
    def __init__(self, tokenizer: TokenizerLike | None = None, counter_name: str | None = None):
        self._tokenizer = tokenizer
        self._counter_name = counter_name

    def count(self, text: str) -> TokenCountResult:
        chars = len(text or "")
        if not text:
            return TokenCountResult(tokens=0, chars=0, counter_name=self.name, is_fallback=self._tokenizer is None)

        if self._tokenizer is None:
            return TokenCountResult(
                tokens=max(1, math.ceil(chars / 2)),
                chars=chars,
                counter_name=self.name,
                is_fallback=True,
            )

        token_ids = self._tokenizer.encode(text, add_special_tokens=False)
        return TokenCountResult(
            tokens=len(token_ids),
            chars=chars,
            counter_name=self.name,
            is_fallback=False,
        )

    @property
    def name(self) -> str:
        if self._counter_name:
            return self._counter_name
        if self._tokenizer is None:
            return "heuristic_chars_div_2"
        return getattr(self._tokenizer, "name_or_path", self._tokenizer.__class__.__name__)


def count_tokens(text: str) -> TokenCountResult:
    return get_token_counter().count(text)


@lru_cache(maxsize=1)
def get_token_counter() -> TokenCounter:
    if settings.tokenizer_provider != "transformers":
        return TokenCounter()

    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(settings.tokenizer_model, local_files_only=True)
    except Exception:
        return TokenCounter()
    return TokenCounter(tokenizer=tokenizer)
