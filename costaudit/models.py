from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StepLog:
    task_id: str
    step: int
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: str = "ok"          # ok | failed
    tool: str = ""
    retries: int = 0

    @staticmethod
    def from_dict(raw: dict[str, Any], position: int) -> "StepLog":
        try:
            return StepLog(
                task_id=str(raw["task_id"]),
                step=int(raw.get("step", position)),
                model=str(raw["model"]),
                input_tokens=int(raw.get("input_tokens", 0)),
                output_tokens=int(raw.get("output_tokens", 0)),
                latency_ms=int(raw.get("latency_ms", 0)),
                status=str(raw.get("status", "ok")),
                tool=str(raw.get("tool", "")),
                retries=int(raw.get("retries", 0)),
            )
        except KeyError as exc:
            raise ValueError(f"log entry {position} missing field {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f"log entry {position} has a non-numeric field: {exc}") from exc


def parse_logs(payload: Any) -> list[StepLog]:
    if isinstance(payload, dict):
        payload = payload.get("steps", payload.get("logs", []))
    if not isinstance(payload, list):
        raise ValueError("logs must be a list or an object with a 'steps' list")
    return [StepLog.from_dict(item, i) for i, item in enumerate(payload)]
