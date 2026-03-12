import sys, os, datetime, json
from flask import Flask, jsonify, redirect, render_template, url_for, request
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import storage
from tester.runner import run_all

app = Flask(__name__, template_folder=os.path.join(HERE, "templates"))
storage.init_db()

_last_run_time = None
RUN_COOLDOWN_SECONDS = 60

@app.route("/")
def index():
    return render_template('consignes.html')

@app.route("/run-page")
def run_page():
    return render_template("run.html")

@app.route("/run")
def run():
    global _last_run_time
    now = datetime.datetime.now(datetime.timezone.utc)
    if _last_run_time is not None:
        elapsed = (now - _last_run_time).total_seconds()
        if elapsed < RUN_COOLDOWN_SECONDS:
            wait = int(RUN_COOLDOWN_SECONDS - elapsed)
            return jsonify({
                "status": "throttled",
                "message": f"Veuillez attendre encore {wait}s avant le prochain run."
            }), 429
    _last_run_time = now
    try:
        result = run_all()
        storage.save_run(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    raw_runs = storage.list_runs(limit=20)
    runs = []
    for r in raw_runs:
        s = r.get("summary", {})
        flat = {
            **r,
            "passed": s.get("passed", 0),
            "failed": s.get("failed", 0),
            "total": s.get("total", 0),
            "error_rate": s.get("error_rate", 0),
            "availability": s.get("availability", 1),
            "latency_avg": s.get("latency_ms_avg", 0),
            "latency_p95": s.get("latency_ms_p95", 0),
            "details": r.get("tests", []),
        }
        runs.append(flat)
    last_run = runs[0] if runs else None
    chart_labels, chart_latency, chart_errors = [], [], []
    for r in reversed(runs[:10]):
        chart_labels.append((r.get("timestamp") or "")[:16].replace("T", " "))
        chart_latency.append(r.get("latency_avg", 0))
        chart_errors.append(round(r.get("error_rate", 0) * 100, 1))
    return render_template("dashboard.html", runs=runs, last_run=last_run,
        chart_labels=chart_labels, chart_latency=chart_latency, chart_errors=chart_errors)

@app.route("/health")
def health():
    runs = storage.list_runs(limit=1)
    last = runs[0] if runs else None
    status, message = "ok", "Aucun run enregistré."
    if last:
        avail = last.get("summary", {}).get("availability", 0)
        message = f"Dernier run : {(last.get('timestamp') or '')[:19]} | disponibilité={round(avail*100,1)}%"
        status = "ok" if avail >= 0.8 else "degraded"
    if request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({"status": status, "message": message, "db": "sqlite", "api": "Jikan (MyAnimeList)"})
    return render_template("health.html")

@app.route("/export")
def export():
    return jsonify(storage.list_runs(limit=100))

if __name__ == "__main__":
    app.run(debug=True)
