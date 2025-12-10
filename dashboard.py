import streamlit as st
import requests
import time

st.set_page_config(page_title="Node2 Dashboard", layout="wide")

CHANNEL_ID = "3197913"
READ_KEY = "92IROMBFRA39V4JA"
API_URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_KEY}&results=1"

# ===================== DASHBOARD =====================
def afficher_dashboard():
    st.title("📡 Node2 - Dashboard temps réel via ThingSpeak")

    try:
        response = requests.get(API_URL).json()

        if "feeds" not in response or len(response["feeds"]) == 0:
            st.error("Aucune donnée trouvée dans ThingSpeak.")
            return

        last = response["feeds"][0]

        temp = last.get("field1", "—")
        hum = last.get("field2", "—")
        ldr = last.get("field3", "—")
        pres = last.get("field4", "0")
        panic = last.get("field5", "0")
        mode = last.get("field6", "—")

        col1, col2, col3 = st.columns(3)
        col1.metric("🌡 Température", temp)
        col2.metric("💧 Humidité", hum)
        col3.metric("🔆 Lumière (LDR)", ldr)

        col4, col5, col6 = st.columns(3)
        col4.write("👤 Présence : " + ("🟢 OUI" if pres == "1" else "⚪ NON"))
        col5.write("🚨 Panic : " + ("🔴 ACTIVÉ" if panic == "1" else "⚪ OFF"))
        col6.write(f"📢 Mode Alarme : `{mode}`")

        st.write("---")
        st.write("📅 Dernière mise à jour :", last.get("created_at", "—"))

    except Exception as e:
        st.error("Impossible de lire ThingSpeak.")
        st.write(e)


# ===================== AUTO REFRESH COMPATIBLE =====================
placeholder = st.empty()

while True:
    with placeholder.container():
        afficher_dashboard()
    time.sleep(3)   # Refresh toutes les 3 secondes
