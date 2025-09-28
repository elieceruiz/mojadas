# app.py
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

def to_datetime_local(dt):
    if not isinstance(dt, datetime):
        dt = parse(dt)
    return dt.astimezone(tz)

# === APP ===
st.subheader("🌧️ Tiempo desde que empezó la mojada")

evento = mojadas_col.find_one({"tipo": "mojada", "en_curso": True})
if evento:
    hora_inicio = to_datetime_local(evento["inicio"])
    segundos_transcurridos = int((datetime.now(tz) - hora_inicio).total_seconds())
    st.success(f"💦 Mojada en curso desde las {hora_inicio.strftime('%H:%M:%S')}")
    cronometro = st.empty()
    stop_button = st.button("⏹️ Finalizar mojada")
    for i in range(segundos_transcurridos, segundos_transcurridos + 100000):
        if stop_button:
            mojadas_col.update_one(
                {"_id": evento["_id"]},
                {"$set": {"fin": datetime.now(tz), "en_curso": False}}
            )
            st.success("✅ Registro finalizado.")
            st.rerun()
        duracion = str(timedelta(seconds=i))
        cronometro.markdown(f"### ⏱️ Duración: {duracion}")
        time.sleep(1)
else:
    if st.button("🟢 Iniciar mojada"):
        mojadas_col.insert_one({
            "tipo": "mojada",
            "inicio": datetime.now(tz),
            "en_curso": True
        })
        st.rerun()

# === HISTORIAL EN EXPANDER ===
with st.expander("📂 Historial de mojadas"):
    registros = list(mojadas_col.find().sort("inicio", -1))
    if registros:
        for i, reg in enumerate(registros, 1):
            inicio = to_datetime_local(reg["inicio"]).strftime("%Y-%m-%d %H:%M:%S")
            fin = reg.get("fin")
            duracion = None
            if fin:
                fin_local = to_datetime_local(fin)
                duracion = str(fin_local - to_datetime_local(reg["inicio"]))
                fin_str = fin_local.strftime("%Y-%m-%d %H:%M:%S")
            else:
                fin_str = "⏳ En curso"
                duracion = "..."

            st.markdown(f"""
            **#{i}**
            - Inicio: `{inicio}`
            - Fin: `{fin_str}`
            - Duración: `{duracion}`
            """)
            if st.button(f"🗑️ Borrar registro #{i}", key=f"del_{reg['_id']}"):
                mojadas_col.delete_one({"_id": reg["_id"]})
                st.warning(f"Registro #{i} eliminado.")
                st.rerun()
    else:
        st.info("No hay registros aún.")
