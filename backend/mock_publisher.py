"""
backend/mock_publisher.py
-------------------------------------------------------------------
Simulates field sensor nodes publishing click-density readings over
MQTT. Use this to test app.py end-to-end (storage, dashboard,
SMS alerts) before real hardware exists.

Requires a local MQTT broker running (e.g. Mosquitto). If you don't
have one installed:
  Windows: download from https://mosquitto.org/download/
  After installing, run `mosquitto` in a separate terminal before
  running this script or app.py.

Run: python mock_publisher.py
-------------------------------------------------------------------
"""

import json
import random
import time

import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

NODES = ["node1", "node2", "node3"]


def main():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print("Publishing mock readings every 5 seconds. Ctrl+C to stop.")
    try:
        while True:
            for node_id in NODES:
                # mostly normal readings, occasionally spike above threshold
                # to test the SMS alert path
                if random.random() < 0.2:
                    click_density = round(random.uniform(5.5, 9.0), 1)  # triggers alert
                else:
                    click_density = round(random.uniform(0.5, 4.5), 1)  # normal

                payload = json.dumps({"click_density": click_density})
                topic = f"xylem/{node_id}/click_density"
                client.publish(topic, payload)
                print(f"Published {topic}: {payload}")

            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped.")
        client.loop_stop()


if __name__ == "__main__":
    main()
