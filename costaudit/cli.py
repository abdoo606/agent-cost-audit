from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import audit
from .models import parse_logs
from .pricing import UnknownModel
from .report import to_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="costaudit", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("audit", help="audit a steps log")
    p.add_argument("--logs", type=Path, required=True)
    p.add_argument("--budget", type=float, default=None)
    p.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.logs.read_text(encoding="utf-8"))
        report = audit(parse_logs(payload), budget_usd=args.budget)
    except (OSError, ValueError, UnknownModel) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "total_cost_usd": report.total_cost_usd,
            "total_steps": report.total_steps,
            "tasks": [t.__dict__ for t in report.tasks],
            "p50_latency_ms": report.p50_latency_ms,
            "p95_latency_ms": report.p95_latency_ms,
            "failures_by_tool": report.failures_by_tool,
            "over_budget": report.over_budget,
        }, indent=2))
    else:
        sys.stdout.write(to_markdown(report))
    return 1 if report.over_budget else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
