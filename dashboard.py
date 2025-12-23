import streamlit as st
import json
import time
import threading
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

if "mqtt_started" not in st.session_state:
    st.session_state.mqtt_started = False

# ================= MQTT THREAD =================
def mqtt_worker():
    def on_connect(client, userdata, flags, rc):
        st.session_state.mqtt_status = "Connecté"
        client.subscribe(MQTT_TOPIC)

    def on_disconnect(client, userdata, rc):
        st.session_state.mqtt_status = "Déconnecté"

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            st.session_state.data.update(payload)
            st.session_state.last_update = time.strftime("%H:%M:%S")
        except:
            pass

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# ================= START MQTT =================
if not st.session_state.mqtt_started:
    threading.Thread(target=mqtt_worker, daemon=True).start()
    st.session_state.mqtt_started = True

# ================= STYLE =================
st.markdown("""
<style>
body { background:#0d1117; }
.title { font-size:36px; font-weight:800; color:#00d4ff; text-align:center; margin-bottom:10px; }
.status { text-align:center; margin-bottom:15px; }
.panel { background:#161b22; padding:20px; border-radius:14px; color:white; }
.msg { padding:12px; border-radius:10px; margin:8px 0; background:#0d1117; }
.ok { color:#00ff4c; font-weight:700; }
.warn { color:#ffe600; font-weight:700; }
.alarm { color:#ff2b2b; font-weight:800; }
.muted { color:#9aa4b2; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>SAS SECURITY – NOEUD 2</div>", unsafe_allow_html=True)

status_color = "ok" if st.session_state.mqtt_status == "Connecté" else "alarm"
st.markdown(
    f"<div class='status {status_color}'>MQTT : {st.session_state.mqtt_status} | "
    f"Dernière mise à jour : {st.session_state.last_update}</div>",
    unsafe_allow_html=True
)

# ================= UI ZONE =================
zone = st.empty()

# ================= UI LOOP =================
while True:
    d = st.session_state.data
    now = time.time()

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

    with zone.container():
        col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

        # ===== ÉTAT SAS =====
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")
            st.markdown(f"<div class='msg ok'>Sécurité {'activée' if system_enabled else 'désactivée'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg ok'>Porte {'ouverte' if door_open else 'fermée'}</div>", unsafe_allow_html=True)
            st.markdown("<div class='msg ok'>Panic disponible</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ===== ÉVÉNEMENTS =====
        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Événements")

            if presence:
                st.markdown("<div class='msg warn'>Présence détectée dans le SAS</div>", unsafe_allow_html=True)
            if temp_alarm:
                st.markdown("<div class='msg alarm'>Température anormalement élevée</div>", unsafe_allow_html=True)
            if mode_alarme == 2:
                st.markdown("<div class='msg alarm'>ALARME DÉCLENCHÉE</div>", unsafe_allow_html=True)
            if panic:
                st.markdown("<div class='msg alarm'>PANIC ACTIVÉ</div>", unsafe_allow_html=True)

            if not any([presence, panic, temp_alarm, mode_alarme == 2]):
                st.markdown("<div class='msg muted'>Aucun événement critique</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ===== CAPTEURS =====
        with col3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")
            st.metric("Température (°C)", temp)
            st.metric("Humidité (%)", hum)
            st.metric("Luminosité (LDR)", ldr)
            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(0.15)  # ⚡ ~150 ms = ULTRA RÉACTIF
