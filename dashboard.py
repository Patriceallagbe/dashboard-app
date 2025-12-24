import streamlit as st
import json
import paho.mqtt.client as mqtt

# ================= CONFIG =================
st.set_page_config(
    page_title="EPHEC – Security Control Room",
    layout="wide"
)

MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883
TOPIC_CMD   = "sas/dashboard/cmd"   # vers Node-RED

# ================= MQTT CLIENT =================
cmd_client = mqtt.Client()
cmd_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ================= UI =================
st.title("🚨 EPHEC – Commande Alarme Globale")

if st.button("🔴 ACTIVER ALARME GLOBALE"):
    cmd_client.publish(
        TOPIC_CMD,
        json.dumps({"global_alarm": 1}),
        qos=1
    )
    st.success("Commande envoyée : global_alarm = 1")
