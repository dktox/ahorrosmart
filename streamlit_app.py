import streamlit as st
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import pandas as pd
from io import BytesIO
import base64
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import io
from PIL import Image
import pytesseract
import cv2
import numpy as np

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="AhorroSMART PRO", layout="wide")
st.title("AhorroSMART PRO - Todo en Uno")

# --- LOGIN CON GOOGLE ---
with open('.streamlit/secrets.toml') as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['google']['client_id'],
    config['google']['client_secret'],
    config['google']['redirect_uris'][0],
    "ahorrosmart"
)

name, authentication_status, username = authenticator.login('Iniciar sesión con Google', 'main')

if not authentication_status:
    st.stop()

st.success(f"¡Bienvenido, {name}!")

# --- INICIALIZAR DATOS ---
if 'ingresos' not in st.session_state:
    st.session_state.ingresos = {"sueldo": 1800, "freelance": 250}
if 'gastos' not in st.session_state:
    st.session_state.gastos = []
if 'categorias' not in st.session_state:
    st.session_state.categorias = {
        "Comida": ["Supermercado", "Restaurantes", "Delivery"],
        "Seguro salud": ["Primas", "Consultas", "Medicamentos"],
        "Movilidad": ["Transporte público", "Taxi/Uber"],
        "Combustible": ["Gasolina"],
        "Seguro coche": ["Póliza", "Reparaciones"],
        "TV": ["Netflix", "Cable"],
        "IA": ["ChatGPT", "Herramientas"]
    }
if 'tasas' not in st.session_state:
    st.session_state.tasas = {"EUR_USD": 1.08, "USD_ARS": 950}

# --- FUNCIÓN COTIZACIONES ---
def obtener_cotizaciones():
    try:
        eur_data = requests.get("https://api.exchangerate-api.com/v4/latest/EUR").json()
        usd_data = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
        st.session_state.tasas["EUR_USD"] = eur_data['rates']['USD']
        st.session_state.tasas["USD_ARS"] = usd_data['rates']['ARS']
        st.success("Cotizaciones actualizadas")
    except:
        st.warning("Usando tasas simuladas")

# --- RELOJES EN VIVO ---
st.subheader("Relojes Mundiales")
tz_ny = pytz.timezone("America/New_York")
tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
tz_esp = pytz.timezone("Europe/Madrid")
now_ny = datetime.now(tz_ny).strftime("%H:%M:%S")
now_arg = datetime.now(tz_arg).strftime("%H:%M:%S")
now_esp = datetime.now(tz_esp).strftime("%H:%M:%S")
col1, col2, col3 = st.columns(3)
col1.metric("Nueva York", now_ny)
col2.metric("Argentina", now_arg)
col3.metric("España", now_esp)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Configuración")
    st.session_state.ingresos["sueldo"] = st.number_input("Sueldo (€)", value=1800.0)
    st.session_state.ingresos["freelance"] = st.number_input("Freelance (€)", value=250.0)
    
    st.subheader("Agregar Categoría")
    nueva_cat = st.text_input("Nombre")
    nuevas_sub = st.text_area("Subcategorías").splitlines()
    if st.button("Agregar") and nueva_cat:
        st.session_state.categorias[nueva_cat] = [s.strip() for s in nuevas_sub if s.strip()]
        st.success(f"Agregada: {nueva_cat}")

    if st.button("Actualizar cotizaciones"):
        obtener_cotizaciones()

# --- COTIZACIONES ---
st.subheader("Cotizaciones")
eur_usd = st.session_state.tasas["EUR_USD"]
usd_ars = st.session_state.tasas["USD_ARS"]
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("USD → ARS", f"1 USD = {usd_ars:,.0f} ARS")
with col2:
    st.metric("EUR → ARS", f"1 EUR = {eur_usd * usd_ars:,.0f} ARS")
with col3:
    st.metric("USDT → ARS", f"1 USDT = {usd_ars:,.0f} ARS")
with col4:
    st.metric("EUR → USDT", f"1 EUR = {eur_usd:.4f} USDT")

# --- ESCANEO DE RECIBOS CON CÁMARA ---
st.subheader("Escanear Recibo")
uploaded_file = st.file_uploader("Sube una foto del recibo", type=["jpg", "png", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Recibo escaneado")
    text = pytesseract.image_to_string(image)
    st.code(text)
    # Extraer monto (simple)
    import re
    montos = re.findall(r'\d+[\.,]\d{2}', text)
    if montos:
        monto = float(montos[-1].replace(',', '.'))
        st.success(f"Monto detectado: €{monto}")
        if st.button("Agregar como gasto"):
            st.session_state.gastos.append({
                "monto": monto, "moneda": "EUR", "monto_eur": monto,
                "cat": "Comida", "sub": "Supermercado", "desc": "Recibo escaneado",
                "fecha": datetime.now().strftime("%d/%m/%Y")
            })

# --- AGREGAR GASTO ---
st.subheader("Agregar Gasto Manual")
c1, c2 = st.columns(2)
with c1:
    monto = st.number_input("Monto", min_value=0.01)
    moneda = st.selectbox("Moneda", ["EUR", "ARS", "USD", "USDT"])
with c2:
    cat = st.selectbox("Categoría", list(st.session_state.categorias.keys()))
    sub = st.selectbox("Subcategoría", st.session_state.categorias[cat])
desc = st.text_input("Descripción")

if st.button("Guardar Gasto"):
    if moneda == "EUR":
        monto_eur = monto
    elif moneda == "ARS":
        monto_eur = monto / (usd_ars * eur_usd)
    elif moneda == "USD":
        monto_eur = monto / eur_usd
    elif moneda == "USDT":
        monto_eur = monto / eur_usd

    st.session_state.gastos.append({
        "monto": monto, "moneda": moneda, "monto_eur": monto_eur,
        "cat": cat, "sub": sub, "desc": desc,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    })
    st.success(f"Guardado: {monto} {moneda}")

    # --- NOTIFICACIÓN POR EMAIL ---
    if monto_eur > 100:
        try:
            msg = MIMEMultipart()
            msg['From'] = config['email']['email']
            msg['To'] = config['email']['email']
            msg['Subject'] = "¡Gasto alto en AhorroSMART!"
            body = f"Has registrado un gasto de €{monto_eur:.2f} en {cat}."
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config['email']['smtp_server'], config['email']['smtp_port'])
            server.starttls()
            server.login(config['email']['email'], config['email']['password'])
            server.send_message(msg)
            server.quit()
            st.info("Email enviado: gasto alto")
        except:
            st.warning("Error al enviar email")

# --- ANÁLISIS ---
if st.session_state.gastos:
    total_ingresos = sum(st.session_state.ingresos.values())
    ahorro_objetivo = 150
    presupuesto = total_ingresos - ahorro_objetivo
    total_gastos = sum(g["monto_eur"] for g in st.session_state.gastos)
    restante = presupuesto - total_gastos

    col1, col2 = st.columns(2)
    col1.metric("Gastado", f"€{total_gastos:,.2f}")
    col2.metric("Restante", f"€{restante:,.2f}")

    # GRÁFICO DE BARRAS
    cats = {}
    for g in st.session_state.gastos:
        cats[g["cat"]] = cats.get(g["cat"], 0) + g["monto_eur"]
    
    if cats:
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(cats.keys(), cats.values(), color='skyblue')
        ax.set_title("Gastos por Categoría (€)")
        ax.set_ylabel("Monto (€)")
        plt.xticks(rotation=45)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h, f'€{h:,.0f}', ha='center', va='bottom')
        st.pyplot(fig)

    # EXPORTAR A EXCEL
    df = pd.DataFrame(st.session_state.gastos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="gastos.xlsx">Descargar Excel</a>'
    st.markdown(href, unsafe_allow_html=True)
