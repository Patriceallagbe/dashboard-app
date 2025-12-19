import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================== CONFIG PAGE ==================
st.set_page_config(page_title="SAS Security Control Room", layout="wide")

# ================== MQTT CONFIG ==================
MQTT_BROKER = "51.103.240.103"
MQTT_PORT = 1883
MQTT_TOPIC = "sas/dashboard/data"
MQTT_CMD_TOPIC = "sas/dashboard/cmd"

# ================== DATA STORE ==================
if "data" not in st.session_state:
    st.session_state.data = {
        "temp": "—",
        "hum": "—",
        "ldr": "—",
        "presence": 0,
        "panic": 0,
        "mode": 0
    }

# ================== MQTT CALLBACK ==================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data.update(payload)
    except:
        pass

# ================== MQTT CLIENT ==================
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

# ================== COMMANDE DISTANTE ==================
def send_alarm_cmd(value):
    payload = json.dumps({"remote_alarm": value})
    client.publish(MQTT_CMD_TOPIC, payload)

# ================== STYLE ==================
st.markdown("""
<style>
body { background-color: #0d1117; }
.big-title {
    font-size: 42px;
    font-weight: 800;
    color: #00d4ff;
    text-align: center;
    padding-bottom: 10px;
}
.panel {
    background-color: #161b22;
    padding: 20px;
    border-radius: 12px;
    color: white;
}
.led-green { color: #00ff4c; font-weight: bold; }
.led-red { color: #ff2b2b; font-weight: bold; }
.led-yellow { color: #ffe600; font-weight: bold; }
.status-title {
    font-size: 22px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ================== TITRE ==================
st.markdown("<div class='big-title'>🛡️ SAS SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

# ================== COMMANDES (UNE SEULE FOIS) ==================
colA, colB, colC = st.columns([1.2, 1.6, 1.2])

with colA:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='status-title'>📡 Commande distante</div>", unsafe_allow_html=True)

    if st.button("🚨 ACTIVER ALERTE"):
        send_alarm_cmd(1)

    if st.button("🛑 STOP ALERTE"):
        send_alarm_cmd(0)

    st.markdown("</div>", unsafe_allow_html=True)

# ================== ZONE RAFRAÎCHIE ==================
zone = st.empty()

while True:
    client.loop()

    d = st.session_state.data

    # 🔴 LOGIQUE ALARME PRIORITAIRE
    alarme_active = (d["mode"] == 1) or (d["panic"] == 1)

    with zone.container():
        c1, c2, c3 = st.columns([1.2, 1.6, 1.2])

        # ---------- ÉTAT ALARME ----------
        with c1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='status-title'>🚨 ALARME</div>", unsafe_allow_html=True)

            if d["panic"] == 1:
                st.markdown("🔴 **PANIC ACTIVÉ**")
            elif d["mode"] == 1:
                st.markdown("🟡 **ALERTE PIR**")
            else:
                st.markdown("🟢 **SYSTÈME NORMAL**")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- ÉTAT DU SAS ----------
        with c2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='status-title'>🏢 ÉTAT DU SAS</div>", unsafe_allow_html=True)

            st.metric("👤 Présence détectée", "OUI" if d["presence"] == 1 else "NON")
            st.metric("📢 Alarme", "ACTIVE" if alarme_active else "INACTIVE")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- CAPTEURS ----------
        with c3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='status-title'>📡 CAPTEURS</div>", unsafe_allow_html=True)

            st.metric("🌡 Température", f"{d['temp']} °C")
            st.metric("💧 Humidité", f"{d['hum']} %")
            st.metric("🔆 LDR", d["ldr"])

            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(1)
