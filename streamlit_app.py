import streamlit as st
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import pandas as pd
from io import BytesIO
import base64
import pytz
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="AhorroSMART", layout="wide")
st.title("AhorroSMART - Gastos + Cotizaciones + Relojes")

# --- CARGAR SECRETS ---
try:
    with open('.streamlit/secrets.toml') as f:
        config = yaml.load(f, Loader=SafeLoader)
except:
    st.error("Falta .streamlit/secrets.toml")
    st.stop()

# --- LOGIN CON GOOGLE ---
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
        "Comida": ["Supermercado", "Restaurantes"],
        "Seguro salud": ["Primas", "Consultas"],
        "Movilidad": ["Transporte", "Taxi"],
        "Combustible": ["Gasolina"],
        "TV": ["Netflix", "Cable"]
    }
if 'tasas' not in st.session_state:
    st.session_state.tasas = {"EUR_USD": 1.08, "USD_ARS": 950}

# --- COTIZACIONES ---
def obtener_cotizaciones():
    try:
        eur = requests.get("https://api.exchangerate-api.com/v4/latest/EUR").json()
        usd = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
        st.session_state.tasas["EUR_USD"] = eur['rates']['USD']
        st.session_state.tasas["USD_ARS"] = usd['rates']['ARS']
        st.success("Cotizaciones actualizadas")
    except:
        st.warning("Usando tasas simuladas")

# --- RELOJES ---
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
    if st.button("Actualizar cotizaciones"):
        obtener_cotizaciones()

# --- COTIZACIONES ---
st.subheader("Cotizaciones")
eur_usd = st.session_state.tasas["EUR_USD"]
usd_ars = st.session_state.tasas["USD_ARS"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("USD → ARS", f"1 USD = {usd_ars:,.0f} ARS")
col2.metric("EUR → ARS", f"1 EUR = {eur_usd * usd_ars:,.0f} ARS")
col3.metric("USDT → ARS", f"1 USDT = {usd_ars:,.0f} ARS")
col4.metric("EUR → USDT", f"1 EUR = {eur_usd:.4f} USDT")

# --- CÁLCULOS ---
total_ingresos = sum(st.session_state.ingresos.values())
ahorro_objetivo = 150
presupuesto = total_ingresos - ahorro_objetivo

col1, col2, col3 = st.columns(3)
col1.metric("Ingresos", f"€{total_ingresos:,.2f}")
col2.metric("Ahorro Objetivo", f"€{ahorro_objetivo}")
col3.metric("Para Gastos", f"€{presupuesto:,.2f}")

# --- AGREGAR GASTO ---
st.subheader("Agregar Gasto")
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
    st.success(f"Guardado: {monto} {moneda} → €{monto_eur:.2f}")

# --- GRÁFICO ---
if st.session_state.gastos:
    total_gastos = sum(g["monto_eur"] for g in st.session_state.gastos)
    restante = presupuesto - total_gastos

    col1, col2 = st.columns(2)
    col1.metric("Gastado", f"€{total_gastos:,.2f}")
    col2.metric("Restante", f"€{restante:,.2f}")

    if restante < 0:
        st.error("¡No alcanzarás los 150€!")
    elif restante < 50:
        st.warning("¡Cuidado!")
    else:
        st.success("¡Vas bien!")

    cats = {}
    for g in st.session_state.gastos:
        cats[g["cat"]] = cats.get(g["cat"], 0) + g["monto_eur"]
    
    if cats:
        fig, ax = plt.subplots()
        bars = ax.bar(cats.keys(), cats.values(), color='skyblue')
        ax.set_title("Gastos por Categoría (€)")
        ax.set_ylabel("Monto (€)")
        plt.xticks(rotation=45)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h, f'€{h:,.0f}', ha='center', va='bottom')
        st.pyplot(fig)

    # EXPORTAR EXCEL
    df = pd.DataFrame(st.session_state.gastos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="gastos.xlsx">Descargar Excel</a>'
    st.markdown(href, unsafe_allow_html=True)
