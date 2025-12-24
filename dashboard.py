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
TOPIC_CMD   = "sas/dashboard/cmd"   # vers Node-RED

# ================= SESSION STATE =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "--:--:--"

# LATCH EVENTS
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
        st.session_state.data.update(payload)
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except:
        pass

if "state_client" not in st.session_state:
    state_client = mqtt.Client()
    state_client.on_connect = on_connect
    state_client.on_message = on_message
    state_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    st.session_state.state_client = state_client
else:
    state_client = st.session_state.state_client

# ================= MQTT CMD CLIENT =================
if "cmd_client" not in st.session_state:
    cmd_client = mqtt.Client()
    cmd_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    st.session_state.cmd_client = cmd_client
else:
    cmd_client = st.session_state.cmd_client

# ================= STYLE =================
st.markdown("""
<style>
body { background:#0d1117; }

.title {
    font-size:38px;
    font-weight:900;
    color:#00d4ff;
    text-align:center;
    margin-bottom:25px;
}

.panel {
    background:#161b22;
    padding:22px;
    border-radius:14px;
    color:white;
}

.msg {
    padding:14px;
    border-radius:12px;
    margin:10px 0;
    font-weight:700;
    background:#0d1117;
}

.ok    { color:#00ff4c; }
.bad   { color:#ff2b2b; }
.warn  { color:#ffe600; }
.muted { color:#9aa4b2; }
</style>
""", unsafe_allow_html=True)

# ================= TITRE =================
st.markdown(
    "<div class='title'>EPHEC – SECURITY CONTROL ROOM</div>",
    unsafe_allow_html=True
)

# ================= COMMANDES DISTANTES =================
st.markdown("## 🚨 Commandes distantes")

if st.button("🔴 ACTIVER ALARME GLOBALE"):
    cmd_client.publish(
        TOPIC_CMD,
        json.dumps({"global_alarm": 1}),
        qos=2
    )
    st.success("Commande ACTIVER envoyée")

st.markdown("---")

# ================= MQTT LOOP (SAFE STREAMLIT) =================
state_client.loop(timeout=0.1)
d = st.session_state.data

# ================= LOGIQUE METIER =================
presence       = int(d.get("presence", 0))
panic          = int(d.get("panic", 0))
temp_alarm     = int(d.get("temp_alarm", 0))
mode_alarme    = int(d.get("mode_alarme", 0))
system_enabled = int(d.get("system_enabled", 0))

temp = d.get("temp", "--")
hum  = d.get("hum", "--")
ldr  = d.get("ldr", "--")

# ===== LATCH =====
if presence == 1:
    st.session_state.presence_latched = 1

if panic == 1:
    st.session_state.panic_latched = 1

if temp_alarm == 1:
    st.session_state.temp_latched = 1

if mode_alarme == 0:
    st.session_state.presence_latched = 0
    st.session_state.panic_latched = 0
    st.session_state.temp_latched = 0

presence_event = st.session_state.presence_latched
panic_event    = st.session_state.panic_latched
temp_event     = st.session_state.temp_latched

alarm_from_node1 = (
    mode_alarme == 2
    and not presence_event
    and not panic_event
    and not temp_event
)

door_open   = (system_enabled == 0)
panic_ready = (panic_event == 0 and mode_alarme == 0)

# ================= AFFICHAGE =================
col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

with col1:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("État du SAS")
    st.markdown(
        f"<div class='msg {'ok' if system_enabled else 'bad'}'>"
        f"{'Sécurité activée' if system_enabled else 'Sécurité désactivée'}</div>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Événements")

    if panic_event:
        st.markdown("<div class='msg bad'>🚨 PANIC ACTIVÉ</div>", unsafe_allow_html=True)
    elif temp_event:
        st.markdown("<div class='msg bad'>🔥 Température critique</div>", unsafe_allow_html=True)
    elif presence_event:
        st.markdown("<div class='msg warn'>⚠️ Présence détectée</div>", unsafe_allow_html=True)
    elif alarm_from_node1:
        st.markdown("<div class='msg bad'>⛔ Accès refusé</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='msg muted'>Aucun événement critique</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Capteurs")
    st.metric("Température (°C)", temp)
    st.metric("Humidité (%)", hum)
    st.metric("Luminosité", ldr)
    st.markdown("</div>", unsafe_allow_html=True)

# ================= RELANCE STREAMLIT =================
time.sleep(0.5)
st.rerun()
