from __future__ import annotations

from .audit import AuditReport


def to_markdown(report: AuditReport) -> str:
    lines = ["# Agent cost audit", "",
             f"Steps: **{report.total_steps}** · tasks: **{len(report.tasks)}** · "
             f"total: **${report.total_cost_usd:.4f}**"]
    if report.budget_usd is not None:
        state = "**OVER BUDGET**" if report.over_budget else "within budget"
        lines.append(f"Budget: ${report.budget_usd:.2f} → {state}")
    lines += ["", f"Latency p50 **{report.p50_latency_ms:.0f} ms** · "
                  f"p95 **{report.p95_latency_ms:.0f} ms**", ""]
    lines += ["| Task | Steps | Cost | Failures | Retries | Retry overhead |",
              "|---|---:|---:|---:|---:|---:|"]
    for task in sorted(report.tasks, key=lambda t: -t.cost_usd):
        lines.append(f"| {task.task_id} | {task.steps} | ${task.cost_usd:.4f} | "
                     f"{task.failures} | {task.retries} | {task.retry_overhead_pct:.0f}% |")
    if report.failures_by_tool:
        lines += ["", "## Failures by tool", "", "| Tool | Failures |", "|---|---:|"]
        lines += [f"| {tool} | {n} |" for tool, n in report.failures_by_tool.items()]
    if report.failures_by_model:
        lines += ["", "## Failures by model", "", "| Model | Failures |", "|---|---:|"]
        lines += [f"| {model} | {n} |" for model, n in report.failures_by_model.items()]
    top = report.top_tasks(3)
    if top:
        lines += ["", "## Where the money went", "",
                  "Top 3 tasks account for "
                  f"**{100 * sum(t.cost_usd for t in top) / report.total_cost_usd:.0f}%** "
                  "of total spend."]
    return "\n".join(lines) + "\n"
