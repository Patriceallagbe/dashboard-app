import streamlit as st
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# ====== Variables globales ======
data = {
    "temp": 0,
    "hum": 0,
    "ldr": 0,
    "presence": False,
    "panic": False,
    "mode_alarme": 0,
    "time": ""
}

# ====== MQTT CALLBACK ======
def on_message(client, userdata, msg):
    global data
    payload = json.loads(msg.payload.decode())
    payload["time"] = datetime.now().strftime("%H:%M:%S")
    data.update(payload)

# ====== MQTT CONFIG ======
MQTT_SERVER = "51.103.240.103"
MQTT_TOPIC = "node2/state"

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)
client.subscribe(MQTT_TOPIC)
client.loop_start()

# ==========================================================
#                 DASHBOARD STREAMLIT
# ==========================================================
st.set_page_config(page_title="ESP32 RTOS - Node2 Dashboard",
                   page_icon="📡",
                   layout="wide")

st.title("📡 Node2 - Dashboard temps réel (Streamlit)")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🌡 Température", f"{data['temp']} °C")

with col2:
    st.metric("💧 Humidité", f"{data['hum']} %")

with col3:
    st.metric("🔆 Lumière (LDR)", data['ldr'])

col4, col5, col6 = st.columns(3)

with col4:
    st.write("👤 Présence :", "🟢 OUI" if data["presence"] else "⚪ NON")

with col5:
    st.write("🚨 Panic Button :", "🔴 ACTIVÉ" if data["panic"] else "⚪ OFF")

with col6:
    st.write("📢 Mode Alarme :", data["mode_alarme"])

st.write("---")
st.write("⏱ Dernière mise à jour :", data["time"])

# Rafraîchissement auto toutes les 1 seconde
st.experimental_rerun()
