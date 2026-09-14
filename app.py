# -*- coding: utf-8 -*-
"""================================================================================
    WEB APP (Flask): dashboard "Activity in English" - ML model comparison.

    Endpoints:
      GET  /                        -> dashboard (HTML)
      GET  /api/results             -> JSON with precomputed results
      POST /api/train               -> starts background re-training
      GET  /api/train/status        -> training status (idle|training|done|error)
      GET  /assets/<file>           -> generated figures (PNG)

    START (local):
        python app.py
        or:  flask --app app run

    PRODUCTION (Render):
        gunicorn app:app --bind 0.0.0.0:$PORT
================================================================================
"""

import os
import json
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(BASE, "app_data", "resultados.json")
ASSETS_DIR = os.path.join(BASE, "static", "assets")

app = Flask(__name__)

_lock = threading.Lock()
_training = {
    "status": "idle",          # idle | training | done | error
    "started": None,
    "finished": None,
    "error": None,
}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_data():
    """Reads the precomputed results JSON (created by precompute.py)."""
    if os.path.exists(DATA_JSON):
        with open(DATA_JSON, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def run_training():
    """Background task: re-runs the full 4-model experiment and updates assets."""
    import precompute  # heavy imports (sklearn/matplotlib) only when needed

    with _lock:
        _training["status"] = "training"
        _training["started"] = _now()
        _training["finished"] = None
        _training["error"] = None

    try:
        # "quick" mode: reduced but representative grids (the official full
        # experiment is committed in app_data via precompute.py). Tips on
        # Render free tier: a full SVC GridSearch can take tens of minutes.
        precompute.run_experiment(
            json_path=DATA_JSON,
            assets_dir=ASSETS_DIR,
            n_jobs=1,          # keep memory/CPU low on Render free tier
            mode=os.environ.get("RETRAIN_MODE", "quick"),
        )
        with _lock:
            _training["status"] = "done"
            _training["finished"] = _now()
    except Exception as exc:  # pragma: no cover
        with _lock:
            _training["status"] = "error"
            _training["error"] = str(exc)
            _training["finished"] = _now()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/results")
def api_results():
    return jsonify(load_data())


@app.post("/api/train")
def api_train():
    with _lock:
        if _training["status"] == "training":
            return jsonify({"status": "training_already_running"}), 200
        thread = threading.Thread(target=run_training, daemon=True)
        thread.start()
        return jsonify({"status": "training_started"}), 202


@app.get("/api/train/status")
def api_status():
    return jsonify(_training)


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)