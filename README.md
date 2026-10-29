# agent-cost-audit

Per-task cost, latency percentiles and failure attribution for agent runs.

Zero dependencies (stdlib only), Python 3.9+.

## Why

"It felt expensive" is not a budget. Once an agent runs 40 steps per task, the
question is which task, which tool and which model is eating the money — and
whether the retries are the cost or the failures are. This turns a steps log
into those answers.

## Usage

```bash
python -m costaudit audit --logs samples/steps.json
python -m costaudit audit --logs samples/steps.json --budget 0.05   # exit 1 if over
python -m costaudit audit --logs samples/steps.json --json
```

Log shape: `{"steps": [{"task_id", "step", "model", "input_tokens",
"output_tokens", "latency_ms", "status", "tool", "retries"}]}`.

## Design notes

- **Unknown models raise** instead of being priced at $0. A silent zero is the
  worst bug in a cost tool.
- **Self-hosted models cost $0 in tokens** and are in the table explicitly, so
  a local Qwen run is comparable rather than invisible.
- **Cost per *success*, not per run**, is the number that decides whether a
  retry-heavy model is actually cheaper.
- **Nearest-rank percentiles** — with 10 steps, interpolated p95 is fiction.

## Tests

```bash
python -m unittest discover -s tests -v
```
