import streamlit as st
import requests
import time

st.set_page_config(page_title="SAS Security Control Room", layout="wide")

CHANNEL_ID = "3197913"
READ_KEY = "92IROMBFRA39V4JA"
API_URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_KEY}&results=1"

# ----- STYLE CSS -----
st.markdown("""
    <style>
    body {
        background-color: #0d1117;
    }
    .big-title {
        font-size: 42px !important;
        font-weight: 800;
        color: #00d4ff !important;
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
    .led-green {
        color: #00ff4c;
        font-weight: bold;
    }
    .led-red {
        color: #ff2b2b;
        font-weight: bold;
    }
    .led-yellow {
        color: #ffe600;
        font-weight: bold;
    }
    .status-title {
        font-size: 22px;
        font-weight: bold;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


# ----- FONCTION DASHBOARD -----
def afficher_dashboard():
    st.markdown("<div class='big-title'>🛡️ SAS SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

    try:
        data = requests.get(API_URL).json()

        if "feeds" not in data or len(data["feeds"]) == 0:
            st.error("Aucune donnée dans ThingSpeak.")
            return

        last = data["feeds"][0]

        temp = last.get("field1", "—")
        hum = last.get("field2", "—")
        ldr = last.get("field3", "—")
        pres = last.get("field4", "0")
        panic = last.get("field5", "0")
        mode = last.get("field6", "0")

        # ====== PANNEAUX ======
        colA, colB, colC = st.columns([1.2, 1.6, 1.2])

        # ------- PANEL ALARME -------
        with colA:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='status-title'>🚨 ALARME</div>", unsafe_allow_html=True)

            if panic == "1":
                st.markdown("🔴 <span class='led-red'>PANIC BUTTON ACTIVÉ</span>", unsafe_allow_html=True)
            else:
                st.markdown("⚪ Panic Button : OFF", unsafe_allow_html=True)

            if mode == "1":
                st.markdown("🟡 <span class='led-yellow'>ALERTE PIR</span>", unsafe_allow_html=True)

            if panic == "0" and mode == "0":
                st.markdown("🟢 <span class='led-green'>Système normal</span>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ------- PANEL CENTRAL : ÉTAT DU SAS -------
        with colB:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='status-title'>🏢 ÉTAT DU SAS</div>", unsafe_allow_html=True)

            st.metric("👤 Présence détectée", "OUI" if pres == "1" else "NON")
            st.metric("📢 Mode Alarme", mode)

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"📅 Dernière mise à jour : **{last.get('created_at', '')}**")

            st.markdown("</div>", unsafe_allow_html=True)

        # ------- PANEL CAPTEURS -------
        with colC:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("<div class='status-title'>📡 CAPTEURS</div>", unsafe_allow_html=True)

            st.metric("🌡 Température", f"{temp} °C")
            st.metric("💧 Humidité", f"{hum} %")
            st.metric("🔆 Lumière (LDR)", ldr)

            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error("Erreur de lecture Thingspeak !")
        st.write(e)


# ----- AUTO REFRESH COMPATIBLE -----
placeholder = st.empty()

while True:
    with placeholder.container():
        afficher_dashboard()
    time.sleep(3)
