"""
Tests "as code" pour l'API Jikan (MyAnimeList).
Chaque fonction retourne :
  { name, status ("PASS"|"FAIL"|"ERROR"), latency_ms, details }
"""

import time
from tester.client import get


# ── A. Tests Contrat (fonctionnels) ──────────────────────────────────────────

def test_get_anime_status_200():
    """GET /anime/11061 → HTTP 200"""
    r = get("/anime/11061")
    ok = r["status_code"] == 200
    return {
        "name": "GET /anime/11061 → HTTP 200",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"status_code={r['status_code']} error={r['error']}" if not ok else ""
    }


def test_get_anime_data_field():
    """GET /anime/11061 retourne du JSON avec champ 'data'"""
    r = get("/anime/11061")
    data = r.get("json") or {}
    ok = r["status_code"] == 200 and "data" in data
    return {
        "name": "GET /anime/11061 → champ 'data' présent",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": "" if ok else f"json keys={list(data.keys())}"
    }


def test_get_anime_required_fields():
    """Champs obligatoires : mal_id, title, type, episodes, score, status"""
    r = get("/anime/11061")
    data = (r.get("json") or {}).get("data", {})
    required = ["mal_id", "title", "type", "episodes", "score", "status"]
    missing = [f for f in required if f not in data]
    ok = r["status_code"] == 200 and len(missing) == 0
    return {
        "name": "GET /anime/11061 → champs obligatoires présents",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"missing={missing}" if missing else ""
    }


def test_get_anime_field_types():
    """Types : mal_id=int, title=str, episodes=int, score=float"""
    r = get("/anime/11061")
    data = (r.get("json") or {}).get("data", {})
    errors = []
    checks = [
        ("mal_id", int),
        ("title", str),
        ("episodes", int),
        ("score", (int, float)),
    ]
    for field, expected in checks:
        val = data.get(field)
        if val is not None and not isinstance(val, expected):
            errors.append(f"{field}={type(val).__name__}")
    ok = r["status_code"] == 200 and not errors
    return {
        "name": "GET /anime/11061 → types des champs corrects",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": "; ".join(errors) if errors else ""
    }


def test_get_anime_invalid_id_404():
    """GET /anime/999999999 → HTTP 404 attendu"""
    r = get("/anime/999999999")
    ok = r["status_code"] == 404
    return {
        "name": "GET /anime/999999999 → HTTP 404",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"status_code={r['status_code']}" if not ok else ""
    }


def test_search_anime_by_query():
    """GET /anime?q=naruto → HTTP 200 + liste non vide"""
    r = get("/anime", params={"q": "naruto", "limit": 3})
    data = r.get("json") or {}
    items = data.get("data", [])
    ok = r["status_code"] == 200 and isinstance(items, list) and len(items) > 0
    return {
        "name": "GET /anime?q=naruto → liste non vide",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"items trouvés={len(items)}"
    }


def test_get_anime_genres_list():
    """GET /anime/11061 → champ 'genres' est une liste"""
    r = get("/anime/11061")
    data = (r.get("json") or {}).get("data", {})
    genres = data.get("genres")
    ok = r["status_code"] == 200 and isinstance(genres, list)
    return {
        "name": "GET /anime/11061 → genres est une liste",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"genres={[g.get('name') for g in genres]}" if isinstance(genres, list) else f"type={type(genres).__name__}"
    }


def test_get_anime_score_range():
    """Score entre 0 et 10"""
    r = get("/anime/11061")
    data = (r.get("json") or {}).get("data", {})
    score = data.get("score")
    ok = r["status_code"] == 200 and score is not None and 0 <= score <= 10
    return {
        "name": "GET /anime/11061 → score dans [0, 10]",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"score={score}"
    }


def test_get_anime_string_id_400_or_404():
    """GET /anime/abc → 400 ou 404 (ID invalide)"""
    r = get("/anime/abc")
    ok = r["status_code"] in (400, 404, 422)
    return {
        "name": "GET /anime/abc → erreur client (400/404/422)",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": r["latency_ms"],
        "details": f"status_code={r['status_code']}"
    }


# ── B. Test QoS (latence sur N appels) ───────────────────────────────────────

def test_latency_multiple_calls(n: int = 5):
    """N appels → avg + p95 latence. Respecte le rate limit Jikan."""
    latencies = []
    errors = 0
    for _ in range(n):
        r = get("/anime/11061")
        latencies.append(r["latency_ms"])
        if r["status_code"] not in (200, 201, 204):
            errors += 1
        time.sleep(0.4)  # max ~2.5 req/s pour rester sous le rate limit

    avg = round(sum(latencies) / len(latencies), 2)
    p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
    error_rate = round(errors / n, 3)
    ok = avg < 4000 and error_rate < 0.5

    return {
        "name": f"QoS latence ({n} appels) — avg={avg}ms p95={p95}ms",
        "status": "PASS" if ok else "FAIL",
        "latency_ms": avg,
        "latency_p95": p95,
        "error_rate": error_rate,
        "details": f"avg={avg}ms p95={p95}ms erreurs={errors}/{n}"
    }


ALL_TESTS = [
    test_get_anime_status_200,
    test_get_anime_data_field,
    test_get_anime_required_fields,
    test_get_anime_field_types,
    test_get_anime_invalid_id_404,
    test_search_anime_by_query,
    test_get_anime_genres_list,
    test_get_anime_score_range,
    test_get_anime_string_id_400_or_404,
    test_latency_multiple_calls,
]
