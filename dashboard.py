import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================= CONFIG =================
st.set_page_config(page_title="SAS Security – Noeud 2", layout="wide")

MQTT_BROKER = "51.103.240.103"
MQTT_PORT = 1883
MQTT_TOPIC = "noeud2/state"

# ================= DATA =================
if "data" not in st.session_state:
    st.session_state.data = {
        "temp": "--",
        "hum": "--",
        "ldr": "--",
        "presence": 0,
        "panic": 0,
        "temp_alarm": 0,
        "mode_alarme": 0,
        "system_enabled": 1,
        "alarm_active": 0,
        "global_alarm": 0
    }

# ================= MQTT =================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        for k in [
            "presence", "panic", "temp_alarm",
            "mode_alarme", "system_enabled",
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
    except:
        pass

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
    margin-bottom: 30px;
}

.panel {
    background-color: #161b22;
    padding: 22px;
    border-radius: 14px;
    color: white;
}

.ok { color: #00ff4c; font-weight: bold; }
.warn { color: #ffe600; font-weight: bold; }
.alarm { color: #ff2b2b; font-weight: bold; }
.info { color: #58a6ff; font-weight: bold; }

.box {
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 10px;
}
.box-ok { border-left: 6px solid #00ff4c; }
.box-warn { border-left: 6px solid #ffe600; }
.box-alarm { border-left: 6px solid #ff2b2b; }
.box-info { border-left: 6px solid #58a6ff; }
</style>
""", unsafe_allow_html=True)

# ================= TITRE =================
st.markdown("<div class='title'>SAS SECURITY – NOEUD 2</div>", unsafe_allow_html=True)

zone = st.empty()

# ================= LOOP =================
while True:
    client.loop()
    d = st.session_state.data

    with zone.container():
        col1, col2, col3 = st.columns(3)

        # ================= COLONNE 1 – ALARMES =================
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Alarmes")

            # PANIC
            if d["panic"]:
                st.markdown("<div class='box box-alarm alarm'>PANIC ACTIVÉ – DANGER IMMÉDIAT</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='box box-ok ok'>PANIC : inactif</div>", unsafe_allow_html=True)

            # ALARME GLOBALE
            if d["global_alarm"]:
                st.markdown("<div class='box box-alarm alarm'>ALARME GLOBALE ACTIVE</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='box box-ok ok'>Alarme globale : inactif</div>", unsafe_allow_html=True)

            # TEMPÉRATURE
            if d["temp_alarm"]:
                st.markdown("<div class='box box-warn warn'>TEMPÉRATURE TROP ÉLEVÉE – RISQUE</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='box box-ok ok'>Température : normale</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ================= COLONNE 2 – ÉTAT SYSTÈME =================
        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du système")

            # SYSTÈME
            if d["system_enabled"]:
                st.markdown("<div class='box box-info info'>Système : ACTIVÉ</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='box box-alarm alarm'>Système : DÉSACTIVÉ</div>", unsafe_allow_html=True)

            # PRÉSENCE
            if d["presence"]:
                st.markdown("<div class='box box-warn warn'>PRÉSENCE DÉTECTÉE DANS LE SAS</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='box box-ok ok'>Aucune présence détectée</div>", unsafe_allow_html=True)

            # ALARME ACTIVE
            if d["alarm_active"]:
                st.markdown("<div class='box box-alarm alarm'>ALARME EN COURS</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='box box-ok ok'>Aucune alarme active</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ================= COLONNE 3 – CAPTEURS =================
        with col3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")

            st.metric("Température (°C)", d["temp"])
            st.metric("Humidité (%)", d["hum"])
            st.metric("Luminosité (LDR)", d["ldr"])

            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(1)
