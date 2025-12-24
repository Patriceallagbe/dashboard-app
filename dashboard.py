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

TOPIC_STATE = "noeud2/state"
TOPIC_CMD   = "sas/dashboard/cmd"

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

# ================= MQTT STATE CLIENT =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_STATE)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data = payload
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except:
        pass

state_client = mqtt.Client(client_id="streamlit_state")
state_client.on_connect = on_connect
state_client.on_message = on_message
state_client.connect(MQTT_BROKER, MQTT_PORT, 60)
state_client.loop_start()

# ================= MQTT CMD CLIENT =================
cmd_client = mqtt.Client(client_id="streamlit_cmd")
cmd_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ================= COMMANDES DISTANTES =================
st.markdown("## 🚨 Commandes distantes")

c1, c2 = st.columns(2)

with c1:
    if st.button("🔴 ACTIVER ALARME GLOBALE"):
        cmd_client.publish(
            TOPIC_CMD,
            json.dumps({"global_alarm": 1}),
            qos=2
        )
        st.success("Commande ACTIVER envoyée")

with c2:
    if st.button("🟢 DÉSACTIVER ALARME GLOBALE"):
        cmd_client.publish(
            TOPIC_CMD,
            json.dumps({"global_alarm": 0}),
            qos=2
        )
        st.success("Commande DÉSACTIVER envoyée")

st.divider()

zone = st.container()

# ================= AFFICHAGE =================
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

    # ===== LATCH =====
    if presence == 1:
        st.session_state.presence_latched = 1

    if panic == 1:
        st.session_state.panic_latched = 1

    if temp_alarm == 1:
        st.session_state.temp_latched = 1

    # RESET uniquement quand alarme arrêtée
    if mode_alarme == 0:
        st.session_state.presence_latched = 0
        st.session_state.panic_latched = 0
        st.session_state.temp_latched = 0

    presence_event = st.session_state.presence_latched
    panic_event    = st.session_state.panic_latched
    temp_event     = st.session_state.temp_latched

    # ===== ALARME NOEUD 1 =====
    alarm_from_node1 = (
        mode_alarme == 2
        and not presence_event
        and not panic_event
        and not temp_event
    )

    # ===== ÉTATS =====
    door_open   = (system_enabled == 0)
    panic_ready = (panic_event == 0 and mode_alarme == 0)

    col1, col2 = st.columns([1.2, 1.8])

    # ================= ÉTAT DU SAS =================
    with col1:
        st.subheader("État du SAS")
        st.write(f"🕒 Dernière mise à jour : {st.session_state.last_update}")
        st.write(f"🌡 Température : {temp} °C")
        st.write(f"💧 Humidité : {hum} %")
        st.write("🔓 Porte ouverte" if door_open else "🔒 SAS sécurisé")

    # ================= ÉVÉNEMENTS =================
    with col2:
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
