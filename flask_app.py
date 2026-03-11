"""
flask_app.py — Application Flask principale.
Déployé sur PythonAnywhere : carlosantiquata.pythonanywhere.com
Routes :
  /          → /dashboard
  /run       → Déclenche un run (anti-spam 60s)
  /dashboard → Tableau de bord + historique
  /health    → Santé de la solution (bonus)
  /export    → Export JSON (bonus)
"""
import sys
import os

# Chemin absolu pour que PythonAnywhere trouve les modules
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import datetime
import json
from flask import Flask, jsonify, redirect, render_template, url_for
import storage
from tester.runner import run_all

app = Flask(__name__, template_folder=os.path.join(HERE, "templates"))

_last_run_time = None
RUN_COOLDOWN_SECONDS = 60

# Init DB au démarrage (prod + local)
storage.init_db()


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


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

    # Aplatir summary dans chaque run pour le template
    runs = []
    for r in raw_runs:
        flat = {**r, **r.get("summary", {}), "details": r.get("tests", [])}
        runs.append(flat)

    last_run = runs[0] if runs else None

    chart_labels = []
    chart_latency = []
    chart_errors = []
    for r in reversed(runs[:10]):
        ts = (r.get("timestamp") or "")[:16].replace("T", " ")
        chart_labels.append(ts)
        chart_latency.append(r.get("latency_ms_avg", 0))
        chart_errors.append(round(r.get("error_rate", 0) * 100, 1))

    return render_template(
        "dashboard.html",
        runs=runs,
        last_run=last_run,
        chart_labels=chart_labels,
        chart_latency=chart_latency,
        chart_errors=chart_errors,
    )


@app.route("/health")
def health():
    runs = storage.list_runs(limit=1)
    last = runs[0] if runs else None
    status = "ok"
    message = "Aucun run enregistré."
    if last:
        summary = last.get("summary", {})
        avail = summary.get("availability", 0)
        message = (
            f"Dernier run : {(last.get('timestamp') or '')[:19]} | "
            f"disponibilité={round(avail * 100, 1)}%"
        )
        status = "ok" if avail >= 0.8 else "degraded"
    return jsonify({
        "status": status,
        "message": message,
        "db": "sqlite",
        "api": "Jikan (MyAnimeList)"
    })


@app.route("/export")
def export():
    data = storage.export_all_json(limit=100)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
