import streamlit as st
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="AhorroSmart", layout="wide")
st.title("AhorroSmart - Control de Gastos + Cotizaciones en Vivo")

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
    st.session_state.tasas = {"EUR_USD": 1.08, "USD_ARS": 950, "USDT_USD": 1.0}

# --- FUNCIÓN PARA COTIZACIONES REALES ---
def obtener_cotizaciones_reales():
    try:
        # EUR/USD de exchangerate-api
        url_eur = "https://api.exchangerate-api.com/v4/latest/EUR"
        data_eur = requests.get(url_eur).json()
        eur_usd = data_eur['rates']['USD']
        st.session_state.tasas["EUR_USD"] = eur_usd

        # USD/ARS de exchangerate-api (tasa de mercado)
        url_ars = "https://api.exchangerate-api.com/v4/latest/USD"
        data_ars = requests.get(url_ars).json()
        usd_ars = data_ars['rates']['ARS']
        st.session_state.tasas["USD_ARS"] = usd_ars

        # USDT/USD ~1 (fijo, ya que es stablecoin)
        st.session_state.tasas["USDT_USD"] = 1.0

        st.success("✅ Cotizaciones actualizadas (exchangerate-api)")
    except:
        st.warning("⚠️ Error de conexión - usando tasas simuladas")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.session_state.ingresos["sueldo"] = st.number_input("Sueldo (€)", value=1800.0)
    st.session_state.ingresos["freelance"] = st.number_input("Freelance (€)", value=250.0)
    if st.button("🔄 Actualizar cotizaciones"):
        obtener_cotizaciones_reales()

# --- COTIZACIONES EN VIVO ---
st.subheader("📈 Cotizaciones en Tiempo Real")
if st.button("Forzar actualización"):
    obtener_cotizaciones_reales()

# Tasas calculadas
eur_usd = st.session_state.tasas["EUR_USD"]
usd_ars = st.session_state.tasas["USD_ARS"]
usdt_usd = st.session_state.tasas["USDT_USD"]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("USD → ARS", f"1 USD = {usd_ars:,.0f} ARS")
    st.metric("ARS → USD", f"1 ARS = {1/usd_ars:.6f} USD")
with col2:
    st.metric("EUR → ARS", f"1 EUR = {eur_usd * usd_ars:,.0f} ARS")
    st.metric("ARS → EUR", f"1 ARS = {1/(eur_usd * usd_ars):.6f} EUR")
with col3:
    st.metric("USDT → ARS", f"1 USDT = {usdt_usd * usd_ars:,.0f} ARS")
    st.metric("ARS → USDT", f"1 ARS = {1/(usdt_usd * usd_ars):.6f} USDT")
with col4:
    st.metric("EUR → USDT", f"1 EUR = {eur_usd / usdt_usd:.4f} USDT")
    st.metric("USDT → EUR", f"1 USDT = {usdt_usd / eur_usd:.4f} EUR")

# --- CÁLCULOS ---
total_ingresos = sum(st.session_state.ingresos.values())
ahorro_objetivo = 150
presupuesto = total_ingresos - ahorro_objetivo

col1, col2, col3 = st.columns(3)
col1.metric("Ingresos", f"€{total_ingresos:,.2f}")
col2.metric("Ahorro Objetivo", f"€{ahorro_objetivo}")
col3.metric("Para Gastos", f"€{presupuesto:,.2f}")

# --- AGREGAR GASTO ---
st.subheader("➕ Agregar Gasto")
c1, c2 = st.columns(2)
with c1:
    monto = st.number_input("Monto", min_value=0.01)
    moneda = st.selectbox("Moneda", ["EUR", "ARS", "USD", "USDT"])
with c2:
    cat = st.selectbox("Categoría", list(st.session_state.categorias.keys()))
    sub = st.selectbox("Subcategoría", st.session_state.categorias[cat])
desc = st.text_input("Descripción")

if st.button("💾 Guardar Gasto"):
    # Convertir a EUR
    if moneda == "EUR":
        monto_eur = monto
    elif moneda == "ARS":
        monto_eur = monto / (usd_ars * eur_usd)
    elif moneda == "USD":
        monto_eur = monto / eur_usd
    elif moneda == "USDT":
        monto_eur = monto / eur_usd  # USDT ~ USD

    st.session_state.gastos.append({
        "monto": monto, "moneda": moneda, "monto_eur": monto_eur,
        "cat": cat, "sub": sub, "desc": desc,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    })
    st.success(f"✅ Guardado: {monto} {moneda} → €{monto_eur:.2f}")

# --- ANÁLISIS ---
if st.session_state.gastos:
    total_gastos = sum(g["monto_eur"] for g in st.session_state.gastos)
    restante = presupuesto - total_gastos

    col1, col2 = st.columns(2)
    col1.metric("Gastado", f"€{total_gastos:.2f}")
    col2.metric("Restante", f"€{restante:.2f}")

    if restante < 0:
        st.error("🚨 ¡No alcanzarás los 150€ de ahorro!")
    elif restante < 50:
        st.warning("⚠️ ¡Cuidado! Ajusta gastos.")
    else:
        st.success("🎉 ¡Vas bien para ahorrar 150€!")

    # Gráfico
    cats = {}
    for g in st.session_state.gastos:
        cats[g["cat"]] = cats.get(g["cat"], 0) + g["monto_eur"]
    if cats:
        fig, ax = plt.subplots()
        ax.pie(cats.values(), labels=cats.keys(), autopct='%1.1f%%')
        ax.set_title("Gastos por Categoría")
        st.pyplot(fig)

# --- CONVERTIDOR RÁPIDO ---
st.subheader("🔄 Convertidor Rápido")
monto_conv = st.number_input("Monto a convertir", min_value=0.0)
de = st.selectbox("De", ["EUR", "ARS", "USD", "USDT"])
a = st.selectbox("A", ["ARS", "EUR", "USD", "USDT"])

if monto_conv > 0 and de != a:
    if de == "EUR":
        if a == "ARS":
            resultado = monto_conv * usd_ars * eur_usd
        elif a == "USD":
            resultado = monto_conv * eur_usd
        elif a == "USDT":
            resultado = monto_conv * eur_usd
    elif de == "ARS":
        if a == "EUR":
            resultado = monto_conv / (usd_ars * eur_usd)
        elif a == "USD":
            resultado = monto_conv / usd_ars
        elif a == "USDT":
            resultado = monto_conv / usd_ars
    elif de == "USD":
        if a == "ARS":
            resultado = monto_conv * usd_ars
        elif a == "EUR":
            resultado = monto_conv / eur_usd
        elif a == "USDT":
            resultado = monto_conv
    elif de == "USDT":
        if a == "ARS":
            resultado = monto_conv * usd_ars
        elif a == "EUR":
            resultado = monto_conv / eur_usd
        elif a == "USD":
            resultado = monto_conv

    st.success(f"**{monto_conv:,.2f} {de} = {resultado:,.2f} {a}**")

# --- EXPORTAR ---
if st.button("📥 Exportar datos"):
    datos = {
        "ingresos": st.session_state.ingresos,
        "gastos": st.session_state.gastos,
        "tasas": st.session_state.tasas
    }
    st.download_button("Descargar JSON", json.dumps(datos, indent=2), "ahorrosmart.json")
