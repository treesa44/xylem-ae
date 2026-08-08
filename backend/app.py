"""
backend/app.py
-------------------------------------------------------------------
Single-file backend: receives click-density readings via MQTT, stores
them in SQLite, serves a dashboard, and fires an SMS alert when a
reading crosses the stress threshold.

Run: python app.py
Then open http://localhost:5000 in a browser.

Uses mock_publisher.py (separate file) to simulate field nodes for
testing -- no real hardware needed to develop and demo this.
-------------------------------------------------------------------
"""

import sqlite3
import time
import threading
import json

from flask import Flask, jsonify, render_template_string
import paho.mqtt.client as mqtt

# ---------------------------------------------------------------
# Config -- adjust as needed
# ---------------------------------------------------------------
DB_PATH = "readings.db"
MQTT_BROKER = "localhost"      # change to your gateway's broker address later
MQTT_PORT = 1883
MQTT_TOPIC = "xylem/+/click_density"   # '+' matches any node ID
CLICK_DENSITY_THRESHOLD = 5.0  # clicks/min -- PLACEHOLDER, tune against real data

# Placeholder farmer phone numbers per node -- replace with real registry later
NODE_PHONE_NUMBERS = {
    "node1": "+91XXXXXXXXXX",
    "node2": "+91XXXXXXXXXX",
}

app = Flask(__name__)


# ---------------------------------------------------------------
# Database
# ---------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            click_density REAL NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            click_density REAL NOT NULL,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_reading(node_id, click_density):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO readings (node_id, click_density, timestamp) VALUES (?, ?, ?)",
        (node_id, click_density, time.time()),
    )
    conn.commit()
    conn.close()


def get_recent_readings(node_id, limit=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT timestamp, click_density FROM readings WHERE node_id=? ORDER BY timestamp ASC LIMIT ?",
        (node_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_node_ids():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT DISTINCT node_id FROM readings")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def log_alert(node_id, click_density, message):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO alerts_log (node_id, click_density, message, timestamp) VALUES (?, ?, ?, ?)",
        (node_id, click_density, message, time.time()),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# SMS -- STUB. Replace send_sms_alert's body with a real Fast2SMS
# or MSG91 API call once you have an API key. Everything else
# (threshold logic, logging) is already wired correctly.
# ---------------------------------------------------------------
def send_sms_alert(node_id, click_density):
    phone = NODE_PHONE_NUMBERS.get(node_id, "unregistered")
    message = (
        f"Field {node_id}: elevated stress signal detected "
        f"({click_density:.1f} clicks/min). Check dashboard for trend."
    )
    # --- Replace below with a real API call, e.g.:
    # import requests
    # requests.post("https://www.fast2sms.com/dev/bulkV2", ...)
    print(f"[SMS STUB] To {phone}: {message}")
    log_alert(node_id, click_density, message)
    return message


def check_and_alert(node_id, click_density):
    if click_density > CLICK_DENSITY_THRESHOLD:
        return send_sms_alert(node_id, click_density)
    return None


# ---------------------------------------------------------------
# MQTT listener -- runs in a background thread alongside Flask
# ---------------------------------------------------------------
def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected (rc={rc}), subscribing to {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)


def on_mqtt_message(client, userdata, msg):
    try:
        node_id = msg.topic.split("/")[1]
        payload = json.loads(msg.payload.decode())
        click_density = float(payload["click_density"])
    except (IndexError, KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"[MQTT] Bad message on {msg.topic}: {e}")
        return

    insert_reading(node_id, click_density)
    check_and_alert(node_id, click_density)
    print(f"[MQTT] {node_id}: {click_density:.1f} clicks/min")


def start_mqtt_listener():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


# ---------------------------------------------------------------
# Dashboard routes
# ---------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Xylem AE Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f5f5f5; }
        .node-card { background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px;
                     box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        h2 { margin-top: 0; }
        canvas { max-width: 100%; }
        @media (max-width: 600px) { body { margin: 10px; } }
    </style>
</head>
<body>
    <h1>Xylem AE Field Monitor</h1>
    <div id="nodes"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <script>
        async function loadDashboard() {
            const res = await fetch('/api/nodes');
            const nodeIds = await res.json();
            const container = document.getElementById('nodes');
            container.innerHTML = '';
            for (const nodeId of nodeIds) {
                const card = document.createElement('div');
                card.className = 'node-card';
                card.innerHTML = `<h2>${nodeId}</h2><canvas id="chart-${nodeId}"></canvas>`;
                container.appendChild(card);

                const dataRes = await fetch(`/api/readings/${nodeId}`);
                const data = await dataRes.json();
                new Chart(document.getElementById(`chart-${nodeId}`), {
                    type: 'line',
                    data: {
                        labels: data.map(d => new Date(d[0]*1000).toLocaleTimeString()),
                        datasets: [{ label: 'Click density (clicks/min)',
                                     data: data.map(d => d[1]), borderColor: '#2E86C1' }]
                    }
                });
            }
            if (nodeIds.length === 0) {
                container.innerHTML = '<p>No readings yet. Run mock_publisher.py to test.</p>';
            }
        }
        loadDashboard();
        setInterval(loadDashboard, 10000);  // refresh every 10s
    </script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/nodes")
def api_nodes():
    return jsonify(get_all_node_ids())


@app.route("/api/readings/<node_id>")
def api_readings(node_id):
    return jsonify(get_recent_readings(node_id))


if __name__ == "__main__":
    init_db()
    mqtt_thread = threading.Thread(target=start_mqtt_listener, daemon=True)
    mqtt_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
