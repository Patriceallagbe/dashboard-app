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
MQTT_TOPIC_STATE = "streamlit/esp32"
MQTT_TOPIC_CMD   = "sas/dashboard/cmd"

# ================= SESSION STATE =================
if "data" not in st.session_state:
    st.session_state.data = {}

# LATCH EVENTS
if "presence_latched" not in st.session_state:
    st.session_state.presence_latched = 0
if "panic_latched" not in st.session_state:
    st.session_state.panic_latched = 0
if "temp_latched" not in st.session_state:
    st.session_state.temp_latched = 0

# ================= MQTT SETUP =================
if "mqtt_client" not in st.session_state:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(MQTT_TOPIC_STATE)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            st.session_state.data.update(payload)
        except:
            pass

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    st.session_state.mqtt_client = client
else:
    client = st.session_state.mqtt_client

# ================= STYLE =================
st.markdown("""
<style>
    .title { font-size:42px; font-weight:900; color:#00d4ff; text-align:center; margin-bottom:20px; }
    .panel { background:#161b22; padding:22px; border-radius:14px; color:white; }
    .msg { padding:14px; border-radius:12px; margin:10px 0; font-weight:700; background:#0d1117; }
    .ok { color:#00ff4c; }
    .bad { color:#ff2b2b; }
    .warn { color:#ffe600; }
    .muted { color:#9aa4b2; }
    
    .stButton > button {
        display: block;
        margin: 0 auto;
        background-color: #ff2b2b;
        color: white;
        border-radius: 10px;
        font-weight: bold;
        padding: 10px 25px;
        border: none;
    }
    .stButton > button:hover {
        background-color: #cc0000;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ================= HEADER & BOUTON =================
st.markdown("<div class='title'>EPHEC – SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 1, 1])
with col_btn_2:
    if st.button("ACTIVER ALARME GLOBALE"):
        client.publish(MQTT_TOPIC_CMD, json.dumps({"global_alarm": 1}), qos=1)

st.divider()

zone = st.empty()

# ================= LOOP =================
while True:
    client.loop(timeout=0.05)
    
    d = st.session_state.data
    presence       = int(d.get("presence", 0))
    panic          = int(d.get("panic", 0))
    temp_alarm     = int(d.get("temp_alarm", 0))
    mode_alarme    = int(d.get("mode_alarme", 0))
    system_enabled = int(d.get("system_enabled", 0))
    temp           = d.get("temp", "--")
    hum            = d.get("hum", "--")
    ldr            = d.get("ldr", "--")

    # Latch Logic
    if presence == 1: st.session_state.presence_latched = 1
    if panic == 1:    st.session_state.panic_latched = 1
    if temp_alarm == 1: st.session_state.temp_latched = 1
    
    if mode_alarme == 0:
        st.session_state.presence_latched = 0
        st.session_state.panic_latched = 0
        st.session_state.temp_latched = 0

    presence_event = st.session_state.presence_latched
    panic_event    = st.session_state.panic_latched
    temp_event     = st.session_state.temp_latched
    
    alarm_from_node1 = (mode_alarme == 2 and not presence_event and not panic_event and not temp_event)
    door_open   = (system_enabled == 0)
    panic_ready = (panic_event == 0 and mode_alarme == 0)

    # Affichage
    with zone.container():
        c1, c2, c3 = st.columns([1.2, 1.8, 1.2])

        with c1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")
            st.markdown(f"<div class='msg {'ok' if system_enabled else 'bad'}'>{'Sécurité activée' if system_enabled else 'Sécurité désactivée'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg {'bad' if door_open else 'ok'}'>{'Porte SAS ouverte' if door_open else 'Porte SAS fermée'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg {'ok' if panic_ready else 'bad'}'>{'Panic disponible' if panic_ready else 'Panic indisponible'}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Événements")
            if panic_event:
                st.markdown("<div class='msg bad'>PANIC ACTIVÉ – Intervention immédiate</div>", unsafe_allow_html=True)
            elif temp_event:
                st.markdown("<div class='msg bad'>Température critique détectée</div>", unsafe_allow_html=True)
            elif presence_event:
                st.markdown("<div class='msg warn'>Présence détectée dans le SAS – DANGER</div>", unsafe_allow_html=True)
            elif alarm_from_node1:
                st.markdown("<div class='msg bad'>Accès refusé – Alarmes actives</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='msg muted'>Aucun événement critique</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")
            st.metric("Température", f"{temp} °C")
            st.metric("Humidité", f"{hum} %")
            st.metric("Luminosité", ldr)
            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(0.4)





