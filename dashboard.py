import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================= CONFIGURATION DE LA PAGE =================
st.set_page_config(
    page_title="EPHEC – Security Control Room",
    layout="wide"
)

# Configuration MQTT
MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883
MQTT_TOPIC_STATE = "noeud2/state"    # Lecture des capteurs
MQTT_TOPIC_CMD   = "sas/dashboard/cmd" # Envoi de commandes (Alarme Globale)

# ================= INITIALISATION DU SESSION STATE =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "--:--:--"

# Événements mémorisés (Latched)
if "presence_latched" not in st.session_state:
    st.session_state.presence_latched = 0
if "panic_latched" not in st.session_state:
    st.session_state.panic_latched = 0
if "temp_latched" not in st.session_state:
    st.session_state.temp_latched = 0

# ================= FONCTIONS MQTT =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC_STATE)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data.update(payload)
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except Exception as e:
        pass

# Initialisation du client unique (st.cache_resource évite de recréer le client à chaque refresh)
@st.cache_resource
def get_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start() # Utilisation de loop_start pour ne pas bloquer Streamlit
    return client

client = get_mqtt_client()

# ================= STYLE CSS CUSTOM =================
st.markdown("""
<style>
    .title {
        font-size:38px;
        font-weight:900;
        color:#00d4ff;
        text-align:center;
        margin-bottom:25px;
    }
    .panel {
        background:#161b22;
        padding:22px;
        border-radius:14px;
        color:white;
        margin-bottom: 15px;
    }
    .msg {
        padding:14px;
        border-radius:12px;
        margin:10px 0;
        font-weight:700;
        background:#0d1117;
    }
    .ok    { color:#00ff4c; }
    .bad   { color:#ff2b2b; }
    .warn  { color:#ffe600; }
    .muted { color:#9aa4b2; }
    
    /* Style spécifique pour le bouton d'alarme */
    div.stButton > button:first-child {
        background-color: #ff2b2b;
        color: white;
        border-radius: 10px;
        width: 100%;
        font-weight: bold;
        border: none;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# ================= INTERFACE UTILISATEUR =================
st.markdown("<div class='title'>EPHEC – SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

# --- SECTION COMMANDE (Fusion du 2ème code) ---
with st.sidebar:
    st.header("🕹️ Commandes")
    if st.button("🔴 ACTIVER ALARME GLOBALE"):
        client.publish(MQTT_TOPIC_CMD, json.dumps({"global_alarm": 1}), qos=1)
        st.success("Commande 'Global Alarm' envoyée !")
    
    st.divider()
    st.info(f"Connecté au Broker: {MQTT_BROKER}")
    st.write(f"Dernière mise à jour: {st.session_state.last_update}")

# Zone dynamique pour les données
zone = st.empty()

# ================= BOUCLE D'AFFICHAGE =================
while True:
    d = st.session_state.data
    
    # Extraction des données
    presence       = int(d.get("presence", 0))
    panic          = int(d.get("panic", 0))
    temp_alarm     = int(d.get("temp_alarm", 0))
    mode_alarme    = int(d.get("mode_alarme", 0))
    system_enabled = int(d.get("system_enabled", 0))
    temp           = d.get("temp", "--")
    hum            = d.get("hum", "--")
    ldr            = d.get("ldr", "--")

    # Logique de Verrouillage (Latch)
    if presence == 1: st.session_state.presence_latched = 1
    if panic == 1:    st.session_state.panic_latched = 1
    if temp_alarm == 1: st.session_state.temp_latched = 1

    # Reset si l'alarme est éteinte
    if mode_alarme == 0:
        st.session_state.presence_latched = 0
        st.session_state.panic_latched = 0
        st.session_state.temp_latched = 0

    presence_event = st.session_state.presence_latched
    panic_event    = st.session_state.panic_latched
    temp_event     = st.session_state.temp_latched

    # Alarme externe (Node 1)
    alarm_from_node1 = (mode_alarme == 2 and not presence_event and not panic_event and not temp_event)

    # États d'affichage
    door_open   = (system_enabled == 0)
    panic_ready = (panic_event == 0 and mode_alarme == 0)

    with zone.container():
        col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

        # --- COLONNE 1 : ÉTAT DU SAS ---
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")
            st.markdown(f"<div class='msg {'ok' if system_enabled else 'bad'}'>{'Sécurité activée' if system_enabled else 'Sécurité désactivée'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg {'bad' if door_open else 'ok'}'>{'Porte SAS ouverte' if door_open else 'Porte SAS fermée'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg {'ok' if panic_ready else 'bad'}'>{'Panic disponible' if panic_ready else 'Panic indisponible'}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- COLONNE 2 : ÉVÉNEMENTS ---
        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Événements Critiques")
            if panic_event:
                st.markdown("<div class='msg bad'>🚨 PANIC ACTIVÉ – Intervention immédiate</div>", unsafe_allow_html=True)
            elif temp_event:
                st.markdown("<div class='msg bad'>🔥 Température critique détectée</div>", unsafe_allow_html=True)
            elif presence_event:
                st.markdown("<div class='msg warn'>⚠️ Présence détectée dans le SAS – DANGER</div>", unsafe_allow_html=True)
            elif alarm_from_node1:
                st.markdown("<div class='msg bad'>⛔ Accès refusé – Code incorrect ou Alarme distante</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='msg muted'>Aucun événement critique</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- COLONNE 3 : CAPTEURS ---
        with col3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")
            st.metric("Température", f"{temp} °C")
            st.metric("Humidité", f"{hum} %")
            st.metric("Luminosité", ldr)
            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(0.5)
