import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================= CONFIG =================
st.set_page_config(
    page_title="EPHEC – Security Control Room",
    layout="wide"
)

MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883
MQTT_TOPIC  = "noeud2/state"

# ================= SESSION STATE =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "--:--:--"

if "presence_latched" not in st.session_state:
    st.session_state.presence_latched = 0

if "panic_latched" not in st.session_state:
    st.session_state.panic_latched = 0

if "temp_latched" not in st.session_state:
    st.session_state.temp_latched = 0

# ================= MQTT =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data = payload
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except:
        pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# ================= UI =================
st.title("🚨 EPHEC – Security Control Room")

zone = st.container()

with zone:
    d = st.session_state.data

    # ===== MQTT DATA =====
    presence       = int(d.get("presence", 0))      # PIR
    panic          = int(d.get("panic", 0))
    temp_alarm     = int(d.get("temp_alarm", 0))
    mode_alarme    = int(d.get("mode_alarme", 0))   # 0 = OFF / 2 = ALARME
    system_enabled = int(d.get("system_enabled", 0))

    temp = d.get("temp", "--")
    hum  = d.get("hum", "--")

    # ===== LATCH EVENTS =====
    if presence == 1:
        st.session_state.presence_latched = 1

    if panic == 1:
        st.session_state.panic_latched = 1

    if temp_alarm == 1:
        st.session_state.temp_latched = 1

    # RESET UNIQUEMENT quand l’alarme est désactivée
    if mode_alarme == 0:
        st.session_state.presence_latched = 0
        st.session_state.panic_latched = 0
        st.session_state.temp_latched = 0

    presence_event = st.session_state.presence_latched
    panic_event    = st.session_state.panic_latched
    temp_event     = st.session_state.temp_latched

    # ===== ALARME PROVENANT DU NOEUD 1 =====
    alarm_from_node1 = (
        mode_alarme == 2
        and not presence_event
        and not temp_alarm
        and not panic_event
        and not temp_event
    )

    # ===== ÉTATS =====
    door_open  = (system_enabled == 0)
    sas_secure = (system_enabled == 1)

    # ================= AFFICHAGE =================
    st.subheader("État du système")
    st.write(f"🕒 Dernière mise à jour : {st.session_state.last_update}")
    st.write(f"🌡 Température : {temp} °C")
    st.write(f"💧 Humidité : {hum} %")

    st.subheader("Événements")

    if panic_event:
        st.error("🚨 PANIC ACTIVÉ – Intervention immédiate")

    elif temp_alarm or temp_event:
        st.error("🔥 Température critique détectée")

    elif presence_event:
        st.warning("⚠️ Présence détectée dans le SAS – DANGER")

    elif alarm_from_node1:
        st.error("⛔ Accès refusé – Code incorrect ou PANIC déclenché au SAS")

    else:
        st.success("✅ Aucun événement critique")
