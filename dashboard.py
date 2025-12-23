import time
import json
import paho.mqtt.client as mqtt

# ================= CONFIG =================
st.set_page_config(
    page_title="EPHEC – Security Control Room",
    layout="wide"
)

MQTT_BROKER = "51.103.240.103"
MQTT_PORT   = 1883
MQTT_TOPIC  = "noeud2/state"

# ================= SESSION =================
if "data" not in st.session_state:
    st.session_state.data = {}

if "last_update" not in st.session_state:
    st.session_state.last_update = "—"

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Déconnecté"

# LATCHS
# LATCH EVENTS
if "presence_latched" not in st.session_state:
    st.session_state.presence_latched = 0

@@ -59,7 +59,7 @@
    font-weight:800;
    color:#00d4ff;
    text-align:center;
    margin-bottom:20px;
    margin-bottom:25px;
}

.panel {
@@ -77,10 +77,10 @@
    font-weight:700;
}

.ok { color:#00ff4c; }
.bad { color:#ff2b2b; }
.ok   { color:#00ff4c; }
.bad  { color:#ff2b2b; }
.warn { color:#ffe600; }
.muted { color:#9aa4b2; }
.muted{ color:#9aa4b2; }
</style>
""", unsafe_allow_html=True)

@@ -97,7 +97,7 @@
    client.loop(timeout=0.1)
    d = st.session_state.data

    # ===== DONNÉES MQTT =====
    # ===== LECTURE MQTT =====
    presence       = int(d.get("presence", 0))
    panic          = int(d.get("panic", 0))
    temp_alarm     = int(d.get("temp_alarm", 0))
@@ -108,30 +108,30 @@
    hum  = d.get("hum", "--")
    ldr  = d.get("ldr", "--")

    # ===== LATCH PRÉSENCE =====
    # ===== LATCH LOGIC =====
    if presence == 1:
        st.session_state.presence_latched = 1
    if mode_alarme == 0 and presence == 0:
        st.session_state.presence_latched = 0

    # ===== LATCH PANIC (LOGIQUE CORRIGÉE) =====
    if panic == 1:
        st.session_state.panic_latched = 1

    # reset latch uniquement quand l’alarme est finie
    if mode_alarme == 0:
        st.session_state.presence_latched = 0
        st.session_state.panic_latched = 0

    presence_event = st.session_state.presence_latched
    panic_event    = st.session_state.panic_latched

    # ===== ÉTATS GLOBAUX =====
    door_open  = (system_enabled == 0)
    sas_secure = (system_enabled == 1)
    # ===== ÉTATS =====
    door_open   = (system_enabled == 0)
    sas_secure  = (system_enabled == 1)
    panic_ready = (panic_event == 0 and mode_alarme == 0)

    with zone.container():
        col1, col2, col3 = st.columns([1.2, 1.8, 1.2])

        # ===== ÉTAT DU SAS =====
        # ================= ÉTAT DU SAS =================
        with col1:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("État du SAS")
@@ -154,38 +154,53 @@
                unsafe_allow_html=True
            )

            # 🔥 PANIC DISPONIBLE / INDISPONIBLE
            st.markdown(
                f"<div class='msg {'bad' if panic_event else 'ok'}'>"
                f"• {'Panic indisponible' if panic_event else 'Panic disponible'}</div>",
                f"<div class='msg {'ok' if panic_ready else 'bad'}'>"
                f"• {'Panic disponible' if panic_ready else 'Panic indisponible'}</div>",
                unsafe_allow_html=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

        # ===== ÉVÉNEMENTS =====
        # ================= ÉVÉNEMENTS =================
        with col2:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Événements")

            if presence_event:
                st.markdown("<div class='msg warn'>• Présence détectée dans le SAS</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='msg warn'>• Présence détectée dans le SAS</div>",
                    unsafe_allow_html=True
                )

            if temp_alarm:
                st.markdown("<div class='msg bad'>• Température anormalement élevée</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='msg bad'>• Température anormalement élevée</div>",
                    unsafe_allow_html=True
                )

            # 🔥 PANIC OU CODE INCORRECT (sans toucher noeud 1)
            if mode_alarme == 2 and not presence_event and not temp_alarm:
                st.markdown(
                    "<div class='msg bad'>• Alarme déclenchée – Code incorrect ou bouton PANIC</div>",
                    unsafe_allow_html=True
                )

            if panic_event:
                st.markdown("<div class='msg bad'>• PANIC ACTIVÉ</div>", unsafe_allow_html=True)

            if mode_alarme == 2:
                st.markdown("<div class='msg bad'>• Alarme déclenchée</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='msg bad'>• PANIC ACTIVÉ</div>",
                    unsafe_allow_html=True
                )

            if not any([presence_event, panic_event, temp_alarm, mode_alarme == 2]):
                st.markdown("<div class='msg muted'>• Aucun événement critique</div>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='msg muted'>• Aucun événement critique</div>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

        # ===== CAPTEURS =====
        # ================= CAPTEURS =================
        with col3:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.subheader("Capteurs")
