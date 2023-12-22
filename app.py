from flask import Flask, jsonify, render_template, Response, request
import threading
import requests
import paho.mqtt.client as mqtt
import time


# Flask Configuration
app = Flask(__name__)

# HiveMQ Configuration
MQTT_BROKER_URL = "broker.hivemq.com"
MQTT_PORT = 8000  # WebSocket port
MQTT_CLIENT_ID = "FlaskClient"
MQTT_TOPIC = 'police/events'  # Vår topic

# Polisens API URL
POLISEN_API_URL = "https://polisen.se/api/events"

#  MQTT client
mqtt_client = mqtt.Client(MQTT_CLIENT_ID, transport="websockets")  

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connecta till HiveMQ broker
mqtt_client.connect(MQTT_BROKER_URL, MQTT_PORT, 60)

# Kör threading och handling
mqtt_client.loop_start()

def fetch_polisen_data():
    while True:
        # Fetch data from Polisen API
        response = requests.get(POLISEN_API_URL)
        events = response.json()  # Assuming the API returns a JSON list

        # Publish to MQTT
        for event in events:
            mqtt_client.publish(MQTT_TOPIC, str(event))
            time.sleep(1)  

        
        time.sleep(600)  

# Hämta Polisens data i en separat thread
threading.Thread(target=fetch_polisen_data, daemon=True).start()

@app.route("/")
def index():
    return jsonify({"status": "Service Running"})

@app.route("/fetch_polisen_data")
def fetch_data():
    event_type = request.args.get("type", "")  # Default till tom sträng om inte angivet
    date = request.args.get("date", "")  # Default till tom sträng om inte angivet

    api_url = "https://polisen.se/api/events"
    if event_type or date:
        params = []
        if event_type:
            params.append(f"type={event_type}")
        if date:
            params.append(f"datetime={date}")
        api_url += "?" + "&".join(params)

    response = requests.get(api_url)
    events = response.json() if response.ok else []
    return jsonify(events)


@app.route("/polisen-events")
def polisen_events():
    response = requests.get("https://polisen.se/api/events")
    events = response.json()
    return render_template("events.html", events=events)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
