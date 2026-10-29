"""Token pricing. USD per 1M tokens, as published at the time of writing.

Prices live in one dict on purpose: when a provider changes them, exactly one
place changes, and every historical report can be regenerated with the price
list of its day.
"""
from __future__ import annotations

DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    # model: (input $/1M, output $/1M)
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-haiku-3.5": (0.80, 4.00),
    "qwen2.5-coder:7b": (0.00, 0.00),  # self-hosted: tokens are free, the GPU is not
    "local-qwen": (0.00, 0.00),
}


class UnknownModel(KeyError):
    """Raised instead of silently pricing an unknown model at zero."""


def cost_usd(input_tokens: int, output_tokens: int, model: str,
             prices: dict[str, tuple[float, float]] | None = None) -> float:
    table = prices if prices is not None else DEFAULT_PRICES
    if input_tokens < 0 or output_tokens < 0:
        raise ValueError("token counts cannot be negative")
    try:
        inp, out = table[model]
    except KeyError as exc:
        raise UnknownModel(f"no price for model {model!r}; add it to the price table") from exc
    return round((input_tokens / 1_000_000) * inp + (output_tokens / 1_000_000) * out, 6)
