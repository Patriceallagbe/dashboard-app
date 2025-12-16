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

# ================== DATA STORE ==================
data_store = {
    "temp": "—",
    "hum": "—",
    "ldr": "—",
    "pres": "0",
    "panic": "0",
    "mode": "0"
}

# ================== MQTT CALLBACK ==================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        data_store.update(payload)
    except:
        pass

# ================== MQTT CLIENT ==================
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)
client.loop_start()

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
    border: 1px solid #30363d;
    color: white;
}
.led-green { color: #00ff4c; font-weight: bold; }
.led-red { color: #ff2b2b; font-weight: bold; }
.led-yellow { color: #ffe600; font-weight: bold; }
.status-title {
    font-size: 22px;
    font-weight: bold;
    padding-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================== DASHBOARD ==================
def afficher_dashboard():
    st.markdown("<div class='big-title'>🛡️ SAS SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

    temp = data_store["temp"]
    hum = data_store["hum"]
    ldr = data_store["ldr"]
    pres = data_store["pres"]
    panic = data_store["panic"]
    mode = data_store["mode"]

    colA, colB, colC = st.columns([1.2, 1.6, 1.2])

    # ---- ALARME ----
    with colA:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='status-title'>🚨 ALARME</div>", unsafe_allow_html=True)

        if panic == "1" or panic == 1:
            st.markdown("🔴 <span class='led-red'>PANIC ACTIVÉ</span>", unsafe_allow_html=True)
        elif mode == "1" or mode == 1:
            st.markdown("🟡 <span class='led-yellow'>ALERTE PIR</span>", unsafe_allow_html=True)
        else:
            st.markdown("🟢 <span class='led-green'>SYSTÈME NORMAL</span>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ---- ETAT SAS ----
    with colB:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='status-title'>🏢 ÉTAT DU SAS</div>", unsafe_allow_html=True)

        st.metric("👤 Présence détectée", "OUI" if pres == "1" or pres == 1 else "NON")
        st.metric("📢 Mode alarme", "ACTIF" if mode == "1" or mode == 1 else "INACTIF")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---- CAPTEURS ----
    with colC:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='status-title'>📡 CAPTEURS</div>", unsafe_allow_html=True)

        st.metric("🌡 Température", f"{temp} °C")
        st.metric("💧 Humidité", f"{hum} %")
        st.metric("🔆 LDR", ldr)

        st.markdown("</div>", unsafe_allow_html=True)

# ================== AUTO REFRESH ==================
placeholder = st.empty()

while True:
    with placeholder.container():
        afficher_dashboard()
    time.sleep(1)
