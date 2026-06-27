import json
import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from influxdb import InfluxDBClient

# Load environment variables
load_dotenv()

print("MQTT Ingest started...", flush=True)

# MQTT
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "admin")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "admin")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensors/+/+")

# InfluxDB
INFLUX_HOST = os.getenv("INFLUXDB_HOST", "influxdb")
INFLUX_PORT = int(os.getenv("INFLUXDB_PORT", 8086))
INFLUX_USERNAME = os.getenv("INFLUXDB_USER", "admin")
INFLUX_PASSWORD = os.getenv("INFLUXDB_PASSWORD", "admin")
INFLUX_DATABASE = os.getenv("INFLUXDB_DB", "sensors")

# Validate configuration
if not MQTT_HOST:
    raise ValueError("MQTT_HOST is not set")

if not INFLUX_HOST:
    raise ValueError("INFLUXDB_HOST is not set")

# InfluxDB Client
influx = InfluxDBClient(
    host=INFLUX_HOST,
    port=INFLUX_PORT,
    username=INFLUX_USERNAME,
    password=INFLUX_PASSWORD,
    database=INFLUX_DATABASE,
)

try:
    influx.ping()
    print("Connected to InfluxDB", flush=True)
except Exception as e:
    print(f"InfluxDB connection failed: {e}", flush=True)
    raise

# MQTT callbacks
def on_connect(client, _userdata, _flags, reason_code, _properties):
    print(f"on_connect called! reason_code={reason_code}", flush=True)

    if reason_code == 0:
        print("MQTT connected successfully!", flush=True)
        print(f"Subscribing to topic: {MQTT_TOPIC}", flush=True)

        client.subscribe(MQTT_TOPIC, qos=1)

    else:
        print(f"MQTT connect failed with code {reason_code}", flush=True)


def on_message(_client, _userdata, msg):
    print(f"Message received: {msg.topic}", flush=True)

    try:
        parts = msg.topic.split("/")

        if len(parts) != 3:
            print(f"Invalid topic: {msg.topic}", flush=True)
            return

        _, location, sensor = parts

        payload = json.loads(msg.payload.decode())

        if "value" not in payload:
            print("Payload missing 'value'", flush=True)
            return

        fields = {}

        for key, value in payload.items():

            if isinstance(value, bool):
                fields[key] = value

            elif isinstance(value, (int, float)):
                fields[key] = value

            elif isinstance(value, str):
                fields[key] = value

            else:
                print(f"Skipping unsupported field: {key}", flush=True)

        json_body = [
            {
                "measurement": "sensors",
                "tags": {
                    "location": location,
                    "sensor": sensor,
                },
                "fields": fields,
            }
        ]

        success = influx.write_points(json_body)

        if not success:
            print("InfluxDB write failed", flush=True)
            return

        print(f"{location}/{sensor} -> {fields}", flush=True)

    except json.JSONDecodeError:
        print("Invalid JSON payload", flush=True)

    except Exception as e:
        print(f"Unexpected error: {e}", flush=True)


def on_disconnect(_client, _userdata, _flags, reason_code, _properties):
    print(f"Disconnected with reason_code: {reason_code}", flush=True)


# MQTT Client
print("Creating MQTT client...", flush=True)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_disconnect = on_disconnect

print(f"Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...", flush=True)

try:
    mqttc.connect(
        MQTT_HOST,
        MQTT_PORT,
        keepalive=60,
    )

    print("Connection initiated, starting loop...", flush=True)

    mqttc.loop_forever()

except KeyboardInterrupt:
    print("Stopping...", flush=True)

finally:
    mqttc.disconnect()