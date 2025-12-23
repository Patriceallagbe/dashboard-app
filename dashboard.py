import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================== CONFIG PAGE ==================
st.set_page_config(
    page_title="SAS Security Control Room",
    layout="wide"
)

# ================== MQTT CONFIG ==================
MQTT_BROKER = "51.103.240.103"
MQTT_PORT = 1883
MQTT_TOPIC = "sas/dashboard/data"
MQTT_CMD_TOPIC = "sas/dashboard/cmd"

# ================== DATA STORE ==================
if "data" not in st.session_state:
    st.session_state.data = {
        "temp": "--",
        "hum": "--",
        "ldr": "--",
        "presence": 0,
        "panic": 0,
        "mode": 0,
        "mode_alarme": 0,
        "temp_alarm": 0,
        "system_enabled": 1,
        "alarm_active": 0,
        "global_alarm": 0
    }

# ================== MQTT CALLBACK ==================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        # compat : mode_alarme -> mode (dashboard legacy)
        if "mode_alarme" in payload:
            payload["mode"] = payload["mode_alarme"]

        # forcer types
        for k in [
            "presence", "panic", "mode", "mode_alarme",
            "temp_alarm", "system_enabled",
            "alarm_active", "global_alarm"
        ]:
            if k in payload:
                payload[k] = int(payload[k])

        if "temp" in payload:
            payload["temp"] = round(float(payload["temp"]), 1)
        if "hum" in payload:
            payload["hum"] = int(payload["hum"])
        if "ldr" in payload:
            payload["ldr"] = int(payload["ldr"])

        st.session_state.data.update(payload)

    except Exception:
        pass

# ================== MQTT CLIENT ==================
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

# ================== COMMANDES DISTANTES ==================
def send_alarm_cmd(value):
    payload = json.dumps({"remote_alarm": value})
    client.publish(MQTT_CMD_TOPIC, payload)

# ================== STYLE ==================
st.markdown("""
<style>
body { background-color: #0d1117; }
.big-title {
    font-size: 40px;
    font-weight: 800;
    color: #00d4ff;
    text-align: center;
    margin-bottom: 20px;
}
.panel {
    background-color: #161b22;
    padding: 20px;
    border-radius: 14px;
    color: white;
}
.status-ok { color: #00ff4c; font-weight: bold; }
.status-warn { color: #ffe600; font-weight: bold; }
.status-alarm { color: #ff2b2b; font-weight: bold; }
.metric {
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ================== TITRE ==================
st.markdown("<div class='big-title'>SAS SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

# ================== COMMANDES ==================
col1, col2, col3 = st.columns([1.2, 1.6, 1.2])

with col1:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Commande distante")

    if st.button("ACTIVER ALARME"):
        send_alarm_cmd(1)

    if st.button("STOP ALARME"):
        send_alarm_cmd(0)

    st.markdown("</div>", unsafe_allow_html=True)

# ================== ZONE DYNAMIQUE ==================
zone = st.empty()

while True:
    client.loop()
    d = st.session_state.data

    # LOGIQUE ALARME CENTRALISÉE
    alarme_active = (
        d.get("alarm_active", 0) == 1 or
        d.get("global_alarm", 0) == 1 or
        d.get("panic", 0) == 1 or
        d.get("mode", 0) == 1
    )

    with zone.container():
        c1, c2, c3 = st.columns(3)

        # ---------- ÉTAT ALARME ----------
        with c1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État Alarme")

            if d["panic"] == 1:
                st.markdown("<div class='status-alarm'>PANIC ACTIVÉ</div>", unsafe_allow_html=True)
            elif d["global_alarm"] == 1:
                st.markdown("<div class='status-alarm'>ALARME GLOBALE</div>", unsafe_allow_html=True)
            elif d["mode"] == 1:
                st.markdown("<div class='status-warn'>ALERTE PIR</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='status-ok'>SYSTÈME NORMAL</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- ÉTAT DU SAS ----------
        with c2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")

            st.metric("Présence", "OUI" if d["presence"] else "NON")
            st.metric("Système", "ACTIF" if d["system_enabled"] else "DÉSACTIVÉ")
            st.metric("Alarme", "ACTIVE" if alarme_active else "INACTIVE")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- CAPTEURS ----------
        with c3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")

            st.metric("Température (°C)", d["temp"])
            st.metric("Humidité (%)", d["hum"])
            st.metric("Luminosité (LDR)", d["ldr"])

            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(1)
