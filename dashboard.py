import streamlit as st
import time
import json
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

def on_disconnect(client, userdata, rc):
    st.session_state.mqtt_status = "Déconnecté"

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
client.on_disconnect = on_disconnect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ================= STYLE =================
st.markdown("""
<style>
body { background-color:#0d1117; }
.title { font-size:36px; font-weight:800; color:#00d4ff; text-align:center; margin-bottom:15px; }
.status { text-align:center; margin-bottom:20px; }
.panel { background:#161b22; padding:22px; border-radius:14px; color:white; }
.msg { padding:14px 16px; border-radius:12px; margin:10px 0; background:#0d1117; }
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

zone = st.empty()

# ================= LOOP PRINCIPALE =================
while True:
    client.loop(timeout=0.1)
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

    # ===== GESTION PORTE =====
    if system_enabled == 0:
        if st.session_state.door_open_until < now:
            st.session_state.door_open_until = now + 5

    door_open = now < st.session_state.door_open_until

    # ===== TEXTES =====
    system_txt = "Sécurité activée" if system_enabled else "Sécurité désactivée"
    security_txt = "SAS sécurisé" if system_enabled else "SAS non sécurisé"
    door_txt = "Porte SAS ouverte" if door_open else "Porte SAS fermée"

    with zone.container():
        col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

        # ===== COLONNE ÉTAT =====
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")
            st.markdown(f"<div class='msg ok'>• {system_txt}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg ok'>• {door_txt}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg ok'>• {security_txt}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg ok'>• Panic disponible</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ===== COLONNE ÉVÉNEMENTS =====
        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Événements")

            if presence:
                st.markdown("<div class='msg warn'>• Présence détectée dans le SAS</div>", unsafe_allow_html=True)

            if mode_alarme == 2:
                st.markdown("<div class='msg alarm'>• Une alarme a été déclenchée</div>", unsafe_allow_html=True)

            if temp_alarm:
                st.markdown("<div class='msg alarm'>• Température anormalement élevée – danger</div>", unsafe_allow_html=True)

            if panic:
                st.markdown("<div class='msg alarm'>• PANIC ACTIVÉ – danger immédiat</div>", unsafe_allow_html=True)

            if not any([presence, panic, temp_alarm, mode_alarme == 2]):
                st.markdown("<div class='msg muted'>• Aucun événement critique</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ===== COLONNE CAPTEURS =====
        with col3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")
            st.metric("Température (°C)", temp)
            st.metric("Humidité (%)", hum)
            st.metric("Luminosité (LDR)", ldr)
            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(1)
