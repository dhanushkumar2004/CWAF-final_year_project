from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import Counter
import json
import os
import csv
import io

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_FILE = os.path.join(BASE_DIR, "waf_logs.json")
CONFIG_FILE = os.path.join(BASE_DIR, "waf_config.json")
PAGE_SIZE = 50

def load_logs():
    logs = []
    if not os.path.exists(LOG_FILE):
        return logs
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except:
                pass
    return logs[-10000:]

def load_config():
    defaults = {
        "enable_sqli": True,
        "enable_xss": True,
        "enable_rate_limit": True,
        "enable_bruteforce": True
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(defaults, f, indent=2)
        return defaults
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**defaults, **json.load(f)}
    except:
        return defaults

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

# SINGLE ROUTE FOR DASHBOARD
@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

@app.route("/api/logs")
def api_logs():
    logs = load_logs()
    logs.reverse()
    page = int(request.args.get("page", 1))
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return jsonify({
        "logs": logs[start:end],
        "total": len(logs),
        "page": page,
        "total_pages": max(1, (len(logs) + PAGE_SIZE - 1) // PAGE_SIZE)
    })

@app.route("/api/stats")
def api_stats():
    logs = load_logs()
    stats = {
        "total": len(logs),
        "blocked": sum(1 for l in logs if l.get("action") == "BLOCKED"),
        "allowed": sum(1 for l in logs if l.get("action") == "ALLOWED"),
        "xss": sum(1 for l in logs if l.get("attack") == "XSS"),
        "sqli": sum(1 for l in logs if l.get("attack") == "SQLi"),
        "bruteforce": sum(1 for l in logs if l.get("attack") == "BruteForce"),
        "ratelimit": sum(1 for l in logs if l.get("attack") == "RateLimit"),
    }
    return jsonify(stats)

@app.route("/api/threats")
def api_threats():
    logs = load_logs()
    threat_map = {}
    for log in logs:
        if log.get("action") == "BLOCKED":
            ip = log.get("ip", "unknown")
            threat_map[ip] = threat_map.get(ip, 0) + 1
    return jsonify({"threat_map": threat_map})

@app.route("/api/charts")
def api_charts():
    now = datetime.now()
    mode = request.args.get("mode", "24h")
    if mode == "today":
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    elif mode == "7d":
        start_time = now - timedelta(days=7)
        end_time = now
    else:
        start_time = now - timedelta(hours=24)
        end_time = now
    logs = load_logs()
    received = 0
    blocked = 0
    timeline = Counter()
    for log in logs:
        try:
            time_str = log["time"]
            if time_str.endswith("Z"):
                time_str = time_str[:-1] + "+00:00"
            t = datetime.fromisoformat(time_str)
        except:
            continue
        if start_time <= t <= end_time:
            received += 1
            if log.get("action") == "BLOCKED":
                blocked += 1
            bucket = t.strftime("%H:%M")
            timeline[bucket] += 1
    labels = sorted(timeline.keys())
    values = [timeline[k] for k in labels]
    return jsonify({
        "received": received,
        "blocked": blocked,
        "labels": labels,
        "values": values
    })

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "GET":
        return jsonify(load_config())
    data = request.json or {}
    cfg = load_config()
    for k in cfg:
        if k in data:
            cfg[k] = bool(data[k])
    save_config(cfg)
    return jsonify({"status": "ok", "config": cfg})

@app.route("/export/json")
def export_json():
    return jsonify(load_logs())

@app.route("/export/csv")
def export_csv():
    logs = load_logs()
    if not logs:
        return Response("", mimetype="text/csv")
    output = io.StringIO()
    fieldnames = ["time", "ip", "method", "url", "attack", "action", "payload"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(logs)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=waf_logs.csv"},
    )

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🛡️  WAF SECURITY DASHBOARD")
    print("=" * 70)
    print(f"📁 Log File:    {LOG_FILE}")
    print(f"⚙️  Config File: {CONFIG_FILE}")
    print(f"🌐 Dashboard:   http://127.0.0.1:5000")
    print(f"📂 Static Folder: {os.path.join(os.path.dirname(__file__), 'static')}")
    print("=" * 70 + "\n")
    
    # Check if index.html exists
    html_file = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
    if os.path.exists(html_file):
        print("✅ index.html found!")
    else:
        print("❌ ERROR: index.html NOT FOUND!")
        print(f"   Expected location: {html_file}")
        print("   Please create dashboard/static/index.html")
    
    print()
    app.run(host="127.0.0.1", port=5000, debug=True)