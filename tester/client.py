import time
import requests

BASE_URL = "https://api.jikan.moe/v4"
TIMEOUT = 5  # secondes
MAX_RETRIES = 1
RETRY_DELAY = 2  # secondes


def get(endpoint: str, params: dict = None) -> dict:
    """
    Effectue un GET sur l'API Jikan avec timeout, retry et gestion 429/5xx.
    Retourne un dict avec : status_code, json, latency_ms, error
    """
    url = f"{BASE_URL}{endpoint}"
    attempt = 0
    last_error = None

    while attempt <= MAX_RETRIES:
        start = time.time()
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            latency_ms = round((time.time() - start) * 1000, 2)

            # Gestion du rate limiting
            if resp.status_code == 429:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    attempt += 1
                    continue
                return {
                    "status_code": 429,
                    "json": None,
                    "latency_ms": latency_ms,
                    "error": "Rate limited (429) apres retry"
                }

            # Gestion erreurs serveur 5xx
            if resp.status_code >= 500:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    attempt += 1
                    continue
                return {
                    "status_code": resp.status_code,
                    "json": None,
                    "latency_ms": latency_ms,
                    "error": f"Erreur serveur ({resp.status_code}) apres retry"
                }

            try:
                data = resp.json()
            except Exception:
                data = None

            return {
                "status_code": resp.status_code,
                "json": data,
                "latency_ms": latency_ms,
                "error": None
            }

        except requests.exceptions.Timeout:
            latency_ms = round((time.time() - start) * 1000, 2)
            last_error = "Timeout"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                attempt += 1
                continue
            return {"status_code": None, "json": None, "latency_ms": latency_ms, "error": "Timeout"}

        except requests.exceptions.RequestException as e:
            latency_ms = round((time.time() - start) * 1000, 2)
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                attempt += 1
                continue
            return {"status_code": None, "json": None, "latency_ms": latency_ms, "error": str(e)}

    return {"status_code": None, "json": None, "latency_ms": 0, "error": last_error or "Erreur inconnue"}
