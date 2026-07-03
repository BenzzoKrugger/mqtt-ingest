# MQTT Ingest

A lightweight Python service that subscribes to MQTT topics and stores sensor data in InfluxDB. It is designed to act as a bridge between IoT devices (ESP32, Arduino, Raspberry Pi, etc.) and a time-series database for visualization in Grafana.

---

## Architecture

```text
           MQTT
ESP32 ─────────────► Mosquitto
                        │
                        ▼
                   mqtt-ingest
                        │
                        │ InfluxDB API
                        ▼
                   InfluxDB
                        │
                        ▼
                    Grafana
```

---

## Features

* Subscribe to MQTT topics
* Parse JSON payloads
* Validate topic structure
* Store data in InfluxDB
* Supports numeric, string and boolean fields
* Simple configuration using environment variables
* Docker-ready

---

## Expected MQTT Topic Format

Topics must follow the format:

```text
sensors/<location>/<sensor>
```

Examples:

```text
sensors/outside/temperature
sensors/outside/humidity
sensors/living_room/co2
sensors/office/light
```

The application extracts:

* **location** → MQTT topic segment 2
* **sensor** → MQTT topic segment 3

These values are stored as InfluxDB tags.

---

## Expected Payload

Payloads must be valid JSON and contain at least the `value` field.

Example:

```json
{
    "value": 23.8
}
```

A richer payload is also supported:

```json
{
    "value": 23.8,
    "battery": 4.07,
    "rssi": -62,
    "status": "ok"
}
```

Supported field types:

* integer
* float
* string
* boolean

Unsupported data types are ignored.

---

## InfluxDB Structure

Measurement:

```text
sensors
```

Tags:

```text
location
sensor
```

Fields:

```text
value
battery
rssi
status
...
```

Example record:

```text
measurement: sensors

tags:
    location = outside
    sensor   = temperature

fields:
    value   = 23.8
    battery = 4.07
    rssi    = -62
```

---

## Configuration

Create a `.env` file based on `.env.example`.

| Variable          | Description             |
| ----------------- | ----------------------- |
| MQTT_HOST         | MQTT broker hostname    |
| MQTT_PORT         | MQTT broker port        |
| MQTT_USERNAME     | MQTT username           |
| MQTT_PASSWORD     | MQTT password           |
| MQTT_TOPIC        | MQTT topic subscription |
| INFLUXDB_HOST     | InfluxDB hostname       |
| INFLUXDB_PORT     | InfluxDB port           |
| INFLUXDB_USER     | InfluxDB username       |
| INFLUXDB_PASSWORD | InfluxDB password       |
| INFLUXDB_DB       | InfluxDB database       |

Example:

```env
MQTT_HOST=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=benzzo
MQTT_PASSWORD=secret_password

MQTT_TOPIC=sensors/+/+

INFLUXDB_HOST=influxdb
INFLUXDB_PORT=8086
INFLUXDB_USER=benzzo
INFLUXDB_PASSWORD=secret_password
INFLUXDB_DB=sensors
```

---

## Running with Docker

```bash
docker compose up -d
```

---

## Running Locally

Install dependencies:

```bash
uv sync
```

Start the application:

```bash
uv run app/main.py
```

---

## Processing Flow

For every received MQTT message:

1. Validate topic format.
2. Decode JSON payload.
3. Verify that the `value` field exists.
4. Filter unsupported field types.
5. Create an InfluxDB point.
6. Write the point into InfluxDB.

---

## Project Structure

```text
mqtt-ingest/
├── app/
│   └── main.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Example Log Output

```text
MQTT Ingest started...
Connected to InfluxDB

Creating MQTT client...
Connecting to MQTT broker...

MQTT connected successfully!
Subscribing to topic: sensors/+/+

Message received: sensors/outside/temperature
outside/temperature -> {'value': 22.5, 'battery': 4.05}
```

---

## Requirements

* Python 3.11+
* MQTT broker (Mosquitto recommended)
* InfluxDB 1.8
* Docker (optional)

---

## Dependencies

* paho-mqtt
* influxdb
* python-dotenv

---

