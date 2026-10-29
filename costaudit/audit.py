"""Aggregation: cost, latency and failure attribution per task and per tool."""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import StepLog
from .pricing import cost_usd
from .stats import percentile


@dataclass
class TaskCost:
    task_id: str
    steps: int
    cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: int
    failures: int
    retries: int

    @property
    def retry_overhead_pct(self) -> float:
        return round(100.0 * self.retries / self.steps, 1) if self.steps else 0.0


@dataclass
class AuditReport:
    tasks: list[TaskCost]
    total_cost_usd: float
    total_steps: int
    p50_latency_ms: float
    p95_latency_ms: float
    failures_by_tool: dict[str, int] = field(default_factory=dict)
    failures_by_model: dict[str, int] = field(default_factory=dict)
    budget_usd: float | None = None

    @property
    def over_budget(self) -> bool:
        return self.budget_usd is not None and self.total_cost_usd > self.budget_usd

    def top_tasks(self, n: int = 3) -> list[TaskCost]:
        return sorted(self.tasks, key=lambda t: t.cost_usd, reverse=True)[:n]

    def cost_per_success(self, passed_task_ids: set[str]) -> float:
        passed = [t for t in self.tasks if t.task_id in passed_task_ids]
        if not passed:
            return float("inf")
        return round(sum(t.cost_usd for t in passed) / len(passed), 6)


def audit(logs: list[StepLog], prices: dict | None = None,
          budget_usd: float | None = None) -> AuditReport:
    if not logs:
        raise ValueError("no logs to audit")

    by_task: dict[str, list[StepLog]] = {}
    for log in logs:
        by_task.setdefault(log.task_id, []).append(log)

    tasks: list[TaskCost] = []
    for task_id, steps in sorted(by_task.items()):
        tasks.append(TaskCost(
            task_id=task_id,
            steps=len(steps),
            cost_usd=round(sum(cost_usd(s.input_tokens, s.output_tokens, s.model, prices)
                               for s in steps), 6),
            input_tokens=sum(s.input_tokens for s in steps),
            output_tokens=sum(s.output_tokens for s in steps),
            latency_ms=sum(s.latency_ms for s in steps),
            failures=sum(1 for s in steps if s.status != "ok"),
            retries=sum(s.retries for s in steps),
        ))

    failed = [s for s in logs if s.status != "ok"]
    by_tool: dict[str, int] = {}
    by_model: dict[str, int] = {}
    for step in failed:
        key = step.tool or "(no tool)"
        by_tool[key] = by_tool.get(key, 0) + 1
        by_model[step.model] = by_model.get(step.model, 0) + 1

    latencies = [float(s.latency_ms) for s in logs]
    return AuditReport(
        tasks=tasks,
        total_cost_usd=round(sum(t.cost_usd for t in tasks), 6),
        total_steps=len(logs),
        p50_latency_ms=percentile(latencies, 50),
        p95_latency_ms=percentile(latencies, 95),
        failures_by_tool=dict(sorted(by_tool.items(), key=lambda kv: -kv[1])),
        failures_by_model=dict(sorted(by_model.items(), key=lambda kv: -kv[1])),
        budget_usd=budget_usd,
    )
