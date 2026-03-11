"""
runner.py — Exécute tous les tests et calcule les métriques du run.
"""

import datetime
from tester.tests import ALL_TESTS


def run_all() -> dict:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results = []
    latencies = []

    for test_fn in ALL_TESTS:
        try:
            result = test_fn()
        except Exception as e:
            result = {
                "name": getattr(test_fn, "__name__", "unknown"),
                "status": "ERROR",
                "latency_ms": 0,
                "details": str(e)
            }
        results.append(result)
        if result.get("latency_ms"):
            latencies.append(result["latency_ms"])

    passed  = sum(1 for r in results if r["status"] == "PASS")
    failed  = sum(1 for r in results if r["status"] == "FAIL")
    errors  = sum(1 for r in results if r["status"] == "ERROR")
    total   = len(results)

    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0
    sorted_lat  = sorted(latencies)
    p95_latency = sorted_lat[max(0, int(len(sorted_lat) * 0.95) - 1)] if sorted_lat else 0
    error_rate  = round((failed + errors) / total, 3) if total > 0 else 0
    availability = round(passed / total, 3) if total > 0 else 0

    return {
        "api": "Jikan (MyAnimeList)",
        "timestamp": timestamp,
        "summary": {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
            "error_rate": error_rate,
            "availability": availability,
            "latency_ms_avg": avg_latency,
            "latency_ms_p95": p95_latency,
        },
        "tests": results
    }
