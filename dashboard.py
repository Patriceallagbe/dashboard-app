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

# ================= SESSION =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "—"

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Déconnecté"

# LATCHS
if "presence_latched" not in st.session_state:
    st.session_state.presence_latched = 0

if "panic_latched" not in st.session_state:
    st.session_state.panic_latched = 0

# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_status = "Connecté"
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data.update(payload)
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except:
        pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ================= STYLE =================
st.markdown("""
<style>
body { background-color:#0d1117; }

.title {
    font-size:36px;
    font-weight:800;
    color:#00d4ff;
    text-align:center;
    margin-bottom:20px;
}

.panel {
    background:#161b22;
    padding:22px;
    border-radius:14px;
    color:white;
}

.msg {
    padding:14px 16px;
    border-radius:12px;
    margin:10px 0;
    background:#0d1117;
    font-weight:700;
}

.ok { color:#00ff4c; }
.bad { color:#ff2b2b; }
.warn { color:#ffe600; }
.muted { color:#9aa4b2; }
</style>
""", unsafe_allow_html=True)

# ================= TITRE =================
st.markdown(
    "<div class='title'>EPHEC – SECURITY CONTROL ROOM</div>",
    unsafe_allow_html=True
)

zone = st.empty()

# ================= LOOP =================
while True:
    client.loop(timeout=0.1)
    d = st.session_state.data

    # ===== DONNÉES MQTT =====
    presence       = int(d.get("presence", 0))
    panic          = int(d.get("panic", 0))
    temp_alarm     = int(d.get("temp_alarm", 0))
    mode_alarme    = int(d.get("mode_alarme", 0))
    system_enabled = int(d.get("system_enabled", 0))

    temp = d.get("temp", "--")
    hum  = d.get("hum", "--")
    ldr  = d.get("ldr", "--")

    # ===== LATCH PRÉSENCE =====
    if presence == 1:
        st.session_state.presence_latched = 1
    if mode_alarme == 0 and presence == 0:
        st.session_state.presence_latched = 0

    # ===== LATCH PANIC (LOGIQUE CORRIGÉE) =====
    if panic == 1:
        st.session_state.panic_latched = 1

    if mode_alarme == 0:
        st.session_state.panic_latched = 0

    presence_event = st.session_state.presence_latched
    panic_event    = st.session_state.panic_latched

    # ===== ÉTATS GLOBAUX =====
    door_open  = (system_enabled == 0)
    sas_secure = (system_enabled == 1)

    with zone.container():
        col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

        # ===== ÉTAT DU SAS =====
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")

            st.markdown(
                f"<div class='msg {'ok' if system_enabled else 'bad'}'>"
                f"• {'Sécurité activée' if system_enabled else 'Sécurité désactivée'}</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div class='msg {'bad' if door_open else 'ok'}'>"
                f"• {'Porte SAS ouverte' if door_open else 'Porte SAS fermée'}</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<div class='msg {'ok' if sas_secure else 'bad'}'>"
                f"• {'SAS sécurisé' if sas_secure else 'SAS non sécurisé'}</div>",
                unsafe_allow_html=True
            )

            # 🔥 PANIC DISPONIBLE / INDISPONIBLE
            st.markdown(
                f"<div class='msg {'bad' if panic_event else 'ok'}'>"
                f"• {'Panic indisponible' if panic_event else 'Panic disponible'}</div>",
                unsafe_allow_html=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

        # ===== ÉVÉNEMENTS =====
        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Événements")

            if presence_event:
                st.markdown("<div class='msg warn'>• Présence détectée dans le SAS</div>", unsafe_allow_html=True)

            if temp_alarm:
                st.markdown("<div class='msg bad'>• Température anormalement élevée</div>", unsafe_allow_html=True)

            if panic_event:
                st.markdown("<div class='msg bad'>• PANIC ACTIVÉ</div>", unsafe_allow_html=True)

            if mode_alarme == 2:
                st.markdown("<div class='msg bad'>• Alarme déclenchée</div>", unsafe_allow_html=True)

            if not any([presence_event, panic_event, temp_alarm, mode_alarme == 2]):
                st.markdown("<div class='msg muted'>• Aucun événement critique</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ===== CAPTEURS =====
        with col3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")
            st.metric("Température (°C)", temp)
            st.metric("Humidité (%)", hum)
            st.metric("Luminosité (LDR)", ldr)
            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(0.5)
