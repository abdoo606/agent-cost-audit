import unittest

from costaudit.audit import audit
from costaudit.models import StepLog, parse_logs
from costaudit.pricing import DEFAULT_PRICES, UnknownModel, cost_usd


class PricingTests(unittest.TestCase):
    def test_cost_math(self):
        # 1000 input @ $3/1M + 500 output @ $15/1M
        self.assertAlmostEqual(cost_usd(1000, 500, "claude-sonnet-4"), 0.003 + 0.0075, places=6)

    def test_self_hosted_model_is_free_in_tokens(self):
        self.assertEqual(cost_usd(1_000_000, 1_000_000, "local-qwen"), 0.0)

    def test_unknown_model_raises_instead_of_zero(self):
        with self.assertRaises(UnknownModel):
            cost_usd(100, 100, "mystery-model")

    def test_custom_price_table(self):
        self.assertAlmostEqual(cost_usd(1_000_000, 0, "x", {"x": (5.0, 5.0)}), 5.0)

    def test_negative_tokens_rejected(self):
        with self.assertRaises(ValueError):
            cost_usd(-1, 0, "gpt-4.1")

    def test_price_table_is_documented_shape(self):
        for model, pair in DEFAULT_PRICES.items():
            self.assertEqual(len(pair), 2, model)


def log(task="t1", step=1, model="claude-sonnet-4", inp=1000, out=500,
        latency=1000, status="ok", tool="bash", retries=0):
    return StepLog(task, step, model, inp, out, latency, status, tool, retries)


class AuditTests(unittest.TestCase):
    def test_groups_by_task_and_totals(self):
        report = audit([log(step=1), log(step=2), log(task="t2", step=1)])
        self.assertEqual(len(report.tasks), 2)
        self.assertEqual(report.total_steps, 3)
        self.assertAlmostEqual(report.total_cost_usd, 3 * (0.003 + 0.0075), places=5)

    def test_failure_buckets(self):
        report = audit([log(status="failed", tool="bash"), log(status="failed", tool="edit_file"),
                        log(status="failed", tool="bash")])
        self.assertEqual(report.failures_by_tool, {"bash": 2, "edit_file": 1})

    def test_retry_overhead(self):
        report = audit([log(step=1, retries=1), log(step=2)])
        self.assertEqual(report.tasks[0].retry_overhead_pct, 50.0)

    def test_percentiles(self):
        report = audit([log(latency=v) for v in (100, 200, 300, 400, 1000)])
        self.assertEqual(report.p50_latency_ms, 300.0)
        self.assertEqual(report.p95_latency_ms, 1000.0)

    def test_top_tasks_sorted_by_cost(self):
        report = audit([log(task="cheap", inp=100, out=10), log(task="pricey", inp=100000, out=9000)])
        self.assertEqual(report.top_tasks(1)[0].task_id, "pricey")

    def test_budget_flag(self):
        self.assertFalse(audit([log()], budget_usd=1.0).over_budget)
        self.assertTrue(audit([log(inp=200000, out=100000)], budget_usd=0.01).over_budget)

    def test_cost_per_success(self):
        report = audit([log(task="a"), log(task="b")])
        self.assertAlmostEqual(report.cost_per_success({"a"}), 0.0105, places=5)
        self.assertEqual(report.cost_per_success(set()), float("inf"))

    def test_empty_logs_rejected(self):
        with self.assertRaises(ValueError):
            audit([])

    def test_parse_logs_accepts_object_or_list(self):
        self.assertEqual(len(parse_logs({"steps": [{"task_id": "t", "model": "gpt-4.1"}]})), 1)
        self.assertEqual(len(parse_logs([{"task_id": "t", "model": "gpt-4.1"}])), 1)

    def test_parse_logs_reports_bad_entry(self):
        with self.assertRaises(ValueError):
            parse_logs([{"model": "gpt-4.1"}])
