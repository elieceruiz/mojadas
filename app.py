from datetime import datetime, timedelta
import time
import pytz
import streamlit as st
from pymongo import MongoClient
from dateutil.parser import parse

# === CONFIGURACIÓN ===
st.set_page_config(page_title="🌧️ Medidor de Mojadas", layout="centered")

# Conexión a Mongo
client = MongoClient(st.secrets["mongo_uri"])
db = client["lluvia"]               # Base de datos
mojadas_col = db["mojadas"]         # Colección de registros

tz = pytz.timezone("America/Bogota")

# --- Utilidad para datetimes ---
def to_datetime_local(dt):
    if not isinstance(dt, datetime):
        dt = parse(dt)
    return dt.astimezone(tz)

# --- Cronómetro enlatado ---
def cronometro_evento(col, tipo_evento, titulo="⏱️ Cronómetro", start_label="🟢 Iniciar", stop_label="⏹️ Finalizar"):
    st.subheader(titulo)

    evento = col.find_one({"tipo": tipo_evento, "en_curso": True})
    if evento:
        hora_inicio = to_datetime_local(evento["inicio"])
        segundos_transcurridos = int((datetime.now(tz) - hora_inicio).total_seconds())
        st.success(f"Evento en curso desde las {hora_inicio.strftime('%H:%M:%S')}")
        cronometro = st.empty()
        stop_button = st.button(stop_label)
        for i in range(segundos_transcurridos, segundos_transcurridos + 100000):
            if stop_button:
                col.update_one(
                    {"_id": evento["_id"]},
                    {"$set": {"fin": datetime.now(tz), "en_curso": False}}
                )
                st.success("✅ Registro finalizado.")
                st.rerun()
            duracion = str(timedelta(seconds=i))
            cronometro.markdown(f"### ⏱️ Duración: {duracion}")
            time.sleep(1)
    else:
        if st.button(start_label):
            col.insert_one({
                "tipo": tipo_evento,
                "inicio": datetime.now(tz),
                "en_curso": True
            })
            st.rerun()

# --- Historial enlatado ---
def historial_eventos(col, tipo_evento, titulo="📂 Historial"):
    with st.expander(titulo):
        registros = list(col.find({"tipo": tipo_evento}).sort("inicio", -1))
        if registros:
            total = len(registros)
            for i, reg in enumerate(registros, 1):
                inicio = to_datetime_local(reg["inicio"]).strftime("%Y-%m-%d %H:%M:%S")
                fin = reg.get("fin")
                if fin:
                    fin_local = to_datetime_local(fin)
                    duracion = str(fin_local - to_datetime_local(reg["inicio"]))
                    fin_str = fin_local.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    fin_str = "⏳ En curso"
                    duracion = "..."

                st.markdown(f"""
                **#{total - i + 1}**
                - Inicio: `{inicio}`
                - Fin: `{fin_str}`
                - Duración: `{duracion}`
                """)
                if st.button(f"🗑️ Borrar registro #{total - i + 1}", key=f"del_{reg['_id']}"):
                    col.delete_one({"_id": reg["_id"]})
                    st.warning(f"Registro #{total - i + 1} eliminado.")
                    st.rerun()
        else:
            st.info("No hay registros aún.")

# --- USO ---
cronometro_evento(
    mojadas_col,
    tipo_evento="mojada",
    titulo="🌧️ Tiempo desde que empezó la mojada",
    start_label="🟢 Iniciar mojada",
    stop_label="⏹️ Finalizar mojada"
)

historial_eventos(
    mojadas_col,
    tipo_evento="mojada",
    titulo="📂 Historial de mojadas"
)
