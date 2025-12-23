import streamlit as st
import json
import time
import paho.mqtt.client as mqtt

# ================= CONFIG =================
st.set_page_config(page_title="SAS Security – Noeud 2", layout="wide")

MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883
MQTT_TOPIC  = "noeud2/state"

# ================= SESSION =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "—"

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Déconnecté"

if "door_open_until" not in st.session_state:
    st.session_state.door_open_until = 0

# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_status = "Connecté"
        client.subscribe(MQTT_TOPIC)
    else:
        st.session_state.mqtt_status = "Erreur connexion"

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data.update(payload)
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except:
        pass

# ================= MQTT CLIENT =================
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ================= UI =================
st.title("SAS SECURITY – NOEUD 2")

# 🔄 BOUTON REFRESH
if st.button("🔄 Rafraîchir les données"):
    client.loop(timeout=1.0)

st.caption(f"MQTT : {st.session_state.mqtt_status} | Dernière mise à jour : {st.session_state.last_update}")

d = st.session_state.data
now = time.time()

# ===== LECTURE SAFE =====
presence = int(d.get("presence", 0) or 0)
panic = int(d.get("panic", 0) or 0)
temp_alarm = int(d.get("temp_alarm", 0) or 0)
mode_alarme = int(d.get("mode_alarme", 0) or 0)
system_enabled = int(d.get("system_enabled", 0) or 0)

temp = d.get("temp", "--")
hum  = d.get("hum", "--")
ldr  = d.get("ldr", "--")

# ===== PORTE SAS (5s) =====
if system_enabled == 0 and st.session_state.door_open_until < now:
    st.session_state.door_open_until = now + 5

door_open = now < st.session_state.door_open_until

col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

# ===== ÉTAT DU SAS =====
with col1:
    st.subheader("État du SAS")
    st.success("Sécurité activée" if system_enabled else "Sécurité désactivée")
    st.info("Porte ouverte" if door_open else "Porte fermée")
    st.info("Panic disponible")

# ===== ÉVÉNEMENTS =====
with col2:
    st.subheader("Événements")

    if presence:
        st.warning("Présence détectée dans le SAS")
    if temp_alarm:
        st.error("Température anormalement élevée")
    if mode_alarme == 2:
        st.error("ALARME DÉCLENCHÉE")
    if panic:
        st.error("PANIC ACTIVÉ")

    if not any([presence, panic, temp_alarm, mode_alarme == 2]):
        st.write("Aucun événement critique")

# ===== CAPTEURS =====
with col3:
    st.subheader("Capteurs")
    st.metric("Température (°C)", temp)
    st.metric("Humidité (%)", hum)
    st.metric("Luminosité (LDR)", ldr)
