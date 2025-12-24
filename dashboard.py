import streamlit as st
import time
import json
import paho.mqtt.client as mqtt

# ================= CONFIGURATION =================
st.set_page_config(
    page_title="EPHEC – Security Control Room",
    layout="wide"
)

MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883

TOPIC_STATE = "noeud2/state"
TOPIC_CMD   = "sas/dashboard/cmd"

# ================= ETAT DE SESSION =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "--:--:--"

# Mémorisation des alertes
for key in ["presence_latched", "panic_latched", "temp_latched"]:
    if key not in st.session_state:
        st.session_state[key] = 0

# ================= MQTT : RÉCEPTION =================
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.data.update(payload)
        st.session_state.last_update = time.strftime("%H:%M:%S")
    except:
        pass

@st.cache_resource
def init_mqtt():
    client = mqtt.Client()
    client.on_connect = lambda c, u, f, rc: c.subscribe(TOPIC_STATE)
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    return client

state_client = init_mqtt()

# ================= MQTT : ENVOI =================
cmd_client = mqtt.Client()
cmd_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# ================= STYLE CSS =================
st.markdown("""
<style>
    .title { font-size:38px; font-weight:900; color:#00d4ff; text-align:center; margin-bottom:20px; }
    .panel { background:#161b22; padding:20px; border-radius:14px; color:white; height:100%; }
    .msg { padding:12px; border-radius:10px; margin:8px 0; font-weight:700; background:#0d1117; }
    .ok { color:#00ff4c; }
    .bad { color:#ff2b2b; }
    .warn { color:#ffe600; }
    .muted { color:#9aa4b2; }
</style>
""", unsafe_allow_html=True)

# ================= INTERFACE =================
st.markdown("<div class='title'>🚨 EPHEC – SECURITY CONTROL ROOM</div>", unsafe_allow_html=True)

# --- BOUTON UNIQUE D'ALARME ---
st.subheader("🎮 Commande d'urgence")
# Un seul bouton large pour l'activation globale
if st.button("🔴 ACTIVER L'ALARME GLOBALE", use_container_width=True):
    cmd_client.publish(TOPIC_CMD, json.dumps({"global_alarm": 1}), qos=1)
    st.toast("SIGNAL D'ALARME ENVOYÉ", icon="🚨")

st.markdown("---")

# Zone dynamique pour les données
placeholder = st.empty()

# ================= LOGIQUE ET BOUCLE =================
while True:
    d = st.session_state.data
    
    # Extraction
    presence       = int(d.get("presence", 0))
    panic          = int(d.get("panic", 0))
    temp_alarm     = int(d.get("temp_alarm", 0))
    mode_alarme    = int(d.get("mode_alarme", 0)) 
    system_enabled = int(d.get("system_enabled", 0))
    temp, hum, ldr = d.get("temp", "--"), d.get("hum", "--"), d.get("ldr", "--")

    # Logique de Latch (Mémorisation)
    if presence == 1: st.session_state.presence_latched = 1
    if panic == 1: st.session_state.panic_latched = 1
    if temp_alarm == 1: st.session_state.temp_latched = 1
    
    # Reset automatique si l'alarme est éteinte sur le matériel
    if mode_alarme == 0:
        st.session_state.presence_latched = 0
        st.session_state.panic_latched = 0
        st.session_state.temp_latched = 0

    with placeholder.container():
        col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

        # 1. État du SAS
        with col1:
            st.markdown("<div class='panel'><h3>État SAS</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg {'ok' if system_enabled else 'bad'}'>{'Sécurité Activée' if system_enabled else 'Sécurité Désactivée'}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg {'bad' if system_enabled == 0 else 'ok'}'>{'Porte Ouverte' if system_enabled == 0 else 'Porte Fermée'}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 2. Événements
        with col2:
            st.markdown("<div class='panel'><h3>Alertes</h3>", unsafe_allow_html=True)
            if st.session_state.panic_latched:
                st.markdown("<div class='msg bad'>🚨 PANIC ACTIVÉ</div>", unsafe_allow_html=True)
            elif st.session_state.temp_latched:
                st.markdown("<div class='msg bad'>🔥 TEMPÉRATURE CRITIQUE</div>", unsafe_allow_html=True)
            elif st.session_state.presence_latched:
                st.markdown("<div class='msg warn'>⚠️ PRÉSENCE DÉTECTÉE</div>", unsafe_allow_html=True)
            elif mode_alarme == 2:
                st.markdown("<div class='msg bad'>⛔ ACCÈS REFUSÉ / ALARME</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='msg muted'>Aucun incident</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 3. Capteurs
        with col3:
            st.markdown("<div class='panel'><h3>Capteurs</h3>", unsafe_allow_html=True)
            st.metric("Température", f"{temp} °C")
            st.metric("Humidité", f"{hum} %")
            st.write(f"Dernière MAJ: {st.session_state.last_update}")
            st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(1)
