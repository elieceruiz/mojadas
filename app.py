# app.py
from datetime import datetime, timedelta
import time
import pytz
import streamlit as st
from pymongo import MongoClient
from dateutil.parser import parse

# === CONFIGURACIÓN ===
st.set_page_config(page_title="🌧️ Lluvia & Dev Tracker", layout="centered")

# Conexión a Mongo
client = MongoClient(st.secrets["mongo_uri"])
db = client["lluvia"]               # Base de datos
dev_col = db["desarrollo"]          # Colección para desarrollo
mojadas_col = db["mojadas"]         # Colección para mojadas

tz = pytz.timezone("America/Bogota")

# Utilidad para convertir cualquier valor a datetime local
def to_datetime_local(dt):
    if not isinstance(dt, datetime):
        dt = parse(str(dt))
    return dt.astimezone(tz)

# === Función neutral de cronómetro enlatado ===
def cronometro_enlatado(col, tipo, label_inicio, label_fin):
    evento = col.find_one({"tipo": tipo, "en_curso": True})
    if evento:
        hora_inicio = to_datetime_local(evento["inicio"])
        segundos_transcurridos = int((datetime.now(tz) - hora_inicio).total_seconds())
        st.success(f"{label_inicio} {hora_inicio.strftime('%H:%M:%S')}")
        cronometro = st.empty()
        stop_button = st.button("⏹️ Finalizar")
        for i in range(segundos_transcurridos, segundos_transcurridos + 100000):
            if stop_button:
                col.update_one(
                    {"_id": evento["_id"]},
                    {"$set": {"fin": datetime.now(tz), "en_curso": False}}
                )
                st.success(label_fin)
                st.rerun()
            duracion = str(timedelta(seconds=i))
            cronometro.markdown(f"### ⏱️ Duración: {duracion}")
            time.sleep(1)
    else:
        if st.button("🟢 Iniciar"):
            col.insert_one({
                "tipo": tipo,
                "inicio": datetime.now(tz),
                "en_curso": True
            })
            st.rerun()

# === INTERFAZ CON TABS ===
tab1, tab2 = st.tabs(["💻 Desarrollo", "🌧️ Mojadas"])

with tab1:
    st.subheader("⏳ Tiempo invertido en el desarrollo de la App")
    cronometro_enlatado(dev_col,
                        tipo="dev_app",
                        label_inicio="🟢 Desarrollo en curso desde",
                        label_fin="✅ Registro de desarrollo finalizado.")

with tab2:
    st.subheader("🌧️ Registro de mojadas por lluvia")
    cronometro_enlatado(mojadas_col,
                        tipo="mojada_lluvia",
                        label_inicio="💦 Te mojaste desde",
                        label_fin="☂️ Registro de mojada finalizado.")
