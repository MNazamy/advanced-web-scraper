import sys
import uuid
import threading
from pathlib import Path

from flask import Flask, request, jsonify, render_template

sys.path.insert(0, str(Path(__file__).parent))

from utils.db_utils import get_topics, create_topic, get_batch_results, get_topic_results
from utils.constants import SEARCH_ENGINES, FILLERS_AND_DISCOURSE_MARKERS

app = Flask(__name__)

_jobs: dict = {}

_SUBSTEP_DEFS = [
    ("scraping",  "Scraping"),
    ("ocr",       "OCR cross-check"),
    ("filter",    "Filter & deduplicate"),
    ("frequency", "Frequency analysis"),
    ("store",     "Store to database"),
]


def _make_steps(engines: list) -> list:
    steps = []
    for e in engines:
        steps.append({
            "id": e,
            "label": e.capitalize(),
            "status": "pending",
            "substeps": [{"id": sid, "label": lbl, "status": "pending", "detail": None} for sid, lbl in _SUBSTEP_DEFS],
        })
    return steps


def _run_job(job_id: str, term: str, engines: list, pages, topic_id):
    steps = _make_steps(engines)
    _jobs[job_id]["steps"] = steps

    # build lookup: engine_id → step dict, substep_id → substep dict
    _engine_map = {s["id"]: s for s in steps}
    _substep_map = {
        e["id"]: {sub["id"]: sub for sub in e.get("substeps", [])}
        for e in steps if "substeps" in e
    }

    def on_step(engine, substep, status, detail=None):
        if engine is None:
            node = _engine_map.get(substep)
        elif substep is None:
            node = _engine_map.get(engine)
        else:
            node = _substep_map.get(engine, {}).get(substep)
        if node:
            node["status"] = status
            if detail is not None:
                node["detail"] = detail

    try:
        from orchestrator import run_pipeline
        batch_id = run_pipeline(term, engines=engines, pages=pages, topic_id=topic_id, on_step=on_step)
        _jobs[job_id].update({"status": "done", "batch_id": batch_id})
    except Exception as e:
        _jobs[job_id].update({"status": "error", "error": str(e)})


@app.route("/")
def index():
    return render_template("index.html", engines=SEARCH_ENGINES, fillers=FILLERS_AND_DISCOURSE_MARKERS)


@app.route("/search", methods=["POST"])
def start_search():
    body = request.json or {}
    term = body.get("term", "").strip()
    engines = body.get("engines", SEARCH_ENGINES)
    pages_raw = body.get("pages", 2)
    if isinstance(pages_raw, dict):
        pages = {e: max(1, min(10, int(pages_raw.get(e, 2)))) for e in engines}
    else:
        n = max(1, min(10, int(pages_raw)))
        pages = {e: n for e in engines}

    topic_id = body.get("topic_id") or None
    if topic_id is not None:
        topic_id = int(topic_id)

    if not term:
        return jsonify({"error": "No search term provided"}), 400

    engines = [e for e in engines if e in SEARCH_ENGINES]
    if not engines:
        return jsonify({"error": "No valid engines selected"}), 400

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "steps": {e: "pending" for e in engines}}
    threading.Thread(target=_run_job, args=(job_id, term, engines, pages, topic_id), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def job_status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job"}), 404
    return jsonify(job)


@app.route("/results/<int:batch_id>")
def get_results(batch_id):
    return jsonify(get_batch_results(batch_id))


@app.route("/topics")
def topics_page():
    return render_template("topics.html")


@app.route("/api/topics", methods=["GET"])
def list_topics():
    return jsonify(get_topics())


@app.route("/api/topics", methods=["POST"])
def api_create_topic():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Topic name is required"}), 400
    topic_id = create_topic(name)
    return jsonify({"topic_id": topic_id, "topic_name": name}), 201


@app.route("/api/topics/<int:topic_id>/results")
def topic_results(topic_id):
    return jsonify(get_topic_results(topic_id))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
