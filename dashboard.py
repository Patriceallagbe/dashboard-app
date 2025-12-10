import streamlit as st
import requests

CHANNEL_ID = "3197913"
API_URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=1"

st.set_page_config(page_title="Node2 Dashboard", layout="wide")
st.title("📡 Node2 - Dashboard temps réel via ThingSpeak")

try:
    data = requests.get(API_URL).json()
    last = data["feeds"][0]

    temp = last["field1"]
    hum = last["field2"]
    ldr = last["field3"]
    pres = last["field4"]
    panic = last["field5"]
    mode = last["field6"]

    col1, col2, col3 = st.columns(3)
    col1.metric("🌡 Température", temp)
    col2.metric("💧 Humidité", hum)
    col3.metric("🔆 Lumière", ldr)

    col4, col5, col6 = st.columns(3)
    col4.write("👤 Présence : " + ("🟢 OUI" if pres == "1" else "⚪ NON"))
    col5.write("🚨 Panic : " + ("🔴 ACTIVÉ" if panic == "1" else "⚪ OFF"))
    col6.write("📢 Mode Alarme : " + str(mode))

    st.write("---")
    st.write("📅 Dernière mise à jour :", last["created_at"])

except Exception as e:
    st.error("Impossible de lire ThingSpeak")
    st.write(e)
