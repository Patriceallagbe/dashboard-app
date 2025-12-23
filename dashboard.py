import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================= CONFIG =================
st.set_page_config(page_title="SAS Security Dashboard", layout="wide")

MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883
MQTT_TOPIC  = "noeud2/state"

# ================= DATA =================
if "data" not in st.session_state:
    st.session_state.data = {
        "temp": "--",
        "hum": "--",
        "ldr": "--",
        "presence": 0,
        "panic": 0,
        "mode_alarme": 0,
        "temp_alarm": 0,
        "system_enabled": 1,
        "alarm_active": 0,
        "global_alarm": 0
    }

# ================= MQTT CALLBACK =================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        # forcer types
        for k in ["presence","panic","mode_alarme","temp_alarm",
                  "system_enabled","alarm_active","global_alarm"]:
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

# ================= MQTT CLIENT =================
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

# ================= STYLE =================
st.markdown("""
<style>
body { background-color: #0d1117; }
.title {
    font-size: 38px;
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
.ok { color: #00ff4c; font-weight: bold; }
.warn { color: #ffe600; font-weight: bold; }
.alarm { color: #ff2b2b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown("<div class='title'>SAS SECURITY – NOEUD 2</div>", unsafe_allow_html=True)

zone = st.empty()

# ================= LOOP =================
while True:
    client.loop()
    d = st.session_state.data

    with zone.container():
        c1, c2, c3 = st.columns(3)

        # -------- ALARME --------
        with c1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État alarme")

            if d["panic"] == 1:
                st.markdown("<div class='alarm'>PANIC ACTIVÉ</div>", unsafe_allow_html=True)
            elif d["global_alarm"] == 1:
                st.markdown("<div class='alarm'>ALARME GLOBALE</div>", unsafe_allow_html=True)
            elif d["mode_alarme"] == 1:
                st.markdown("<div class='warn'>ALERTE PIR</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ok'>SYSTÈME NORMAL</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # -------- ÉTAT SAS --------
        with c2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du système")

            st.metric("Système", "ON" if d["system_enabled"] else "OFF")
            st.metric("Présence", "OUI" if d["presence"] else "NON")
            st.metric("Alarme active", "OUI" if d["alarm_active"] else "NON")

            st.markdown("</div>", unsafe_allow_html=True)

        # -------- CAPTEURS --------
        with c3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")

            st.metric("Température (°C)", d["temp"])
            st.metric("Humidité (%)", d["hum"])
            st.metric("LDR", d["ldr"])

            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(1)
