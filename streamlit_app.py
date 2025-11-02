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
    st.session_state.tasas = {"EUR": 1.0, "ARS": 950.0, "USD": 0.92, "USDT": 1.0}

# --- FUNCIÓN PARA COTIZACIONES BINANCE ---
def obtener_cotizaciones_binance():
    try:
        # ARSUSDT
        ars_data = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ARSUSDT").json()
        ars_price = float(ars_data['price'])
        st.session_state.tasas["ARS"] = ars_price  # 1 USDT = X ARS

        # EURUSDT
        eur_data = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT").json()
        eur_price = float(eur_data['price'])
        st.session_state.tasas["USDT"] = eur_price  # 1 EUR = X USDT

        # Calcular derivados
        st.session_state.tasas["USD"] = 1 / ars_price  # 1 ARS = X USD
        st.session_state.tasas["EUR"] = eur_price / ars_price  # 1 ARS = X EUR

        st.success("Cotizaciones actualizadas desde Binance")
    except:
        st.warning("Error de conexión - usando tasas simuladas")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Configuración")
    st.session_state.ingresos["sueldo"] = st.number_input("Sueldo (€)", value=1800.0)
    st.session_state.ingresos["freelance"] = st.number_input("Freelance (€)", value=250.0)
    if st.button("Actualizar cotizaciones (Binance)"):
        obtener_cotizaciones_binance()

# --- COTIZACIONES EN VIVO ---
st.subheader("Cotizaciones en Tiempo Real (Binance)")
if st.button("Forzar actualización"):
    obtener_cotizaciones_binance()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("USDT → ARS", f"1 USDT = {st.session_state.tasas['ARS']:,.0f} ARS")
    st.metric("ARS → USDT", f"1 ARS = {1/st.session_state.tasas['ARS']:.6f} USDT")
with col2:
    st.metric("EUR → ARS", f"1 EUR = {st.session_state.tasas['ARS'] * st.session_state.tasas['USDT']:,.0f} ARS")
    st.metric("ARS → EUR", f"1 ARS = {1/(st.session_state.tasas['ARS'] * st.session_state.tasas['USDT']):.6f} EUR")
with col3:
    st.metric("USD → ARS", f"1 USD = {st.session_state.tasas['ARS']:,.0f} ARS")
    st.metric("ARS → USD", f"1 ARS = {1/st.session_state.tasas['ARS']:.6f} USD")
with col4:
    st.metric("EUR → USDT", f"1 EUR = {st.session_state.tasas['USDT']:.4f} USDT")
    st.metric("USDT → EUR", f"1 USDT = {1/st.session_state.tasas['USDT']:.4f} EUR")

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
    # Convertir a EUR
    if moneda == "EUR":
        monto_eur = monto
    elif moneda == "ARS":
        monto_eur = monto / (st.session_state.tasas["ARS"] * st.session_state.tasas["USDT"])
    elif moneda == "USD":
        monto_eur = monto / st.session_state.tasas["ARS"]
    elif moneda == "USDT":
        monto_eur = monto * st.session_state.tasas["USDT"]

    st.session_state.gastos.append({
        "monto": monto, "moneda": moneda, "monto_eur": monto_eur,
        "cat": cat, "sub": sub, "desc": desc,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    })
    st.success(f"Guardado: {monto} {moneda} → €{monto_eur:.2f}")

# --- ANÁLISIS ---
if st.session_state.gastos:
    total_gastos = sum(g["monto_eur"] for g in st.session_state.gastos)
    restante = presupuesto - total_gastos

    col1, col2 = st.columns(2)
    col1.metric("Gastado", f"€{total_gastos:.2f}")
    col2.metric("Restante", f"€{restante:.2f}")

    if restante < 0:
        st.error("¡No alcanzarás los 150€ de ahorro!")
    elif restante < 50:
        st.warning("¡Cuidado! Ajusta gastos.")
    else:
        st.success("¡Vas bien para ahorrar 150€!")

    # Gráfico
    cats = {g["cat"]: 0 for g in st.session_state.gastos}
    for g in st.session_state.gastos:
        cats[g["cat"]] += g["monto_eur"]
    if cats:
        fig, ax = plt.subplots()
        ax.pie(cats.values(), labels=cats.keys(), autopct='%1.1f%%')
        ax.set_title("Gastos por Categoría")
        st.pyplot(fig)

# --- CONVERTIDOR RÁPIDO ---
st.subheader("Convertidor Rápido")
monto_conv = st.number_input("Monto a convertir", min_value=0.0)
de = st.selectbox("De", ["EUR", "ARS", "USD", "USDT"], key="de")
a = st.selectbox("A", ["ARS", "EUR", "USD", "USDT"], key="a")

if monto_conv > 0:
    if de == a:
        resultado = monto_conv
    elif de == "EUR" and a == "ARS":
        resultado = monto_conv * st.session_state.tasas["ARS"] * st.session_state.tasas["USDT"]
    elif de == "ARS" and a == "EUR":
        resultado = monto_conv / (st.session_state.tasas["ARS"] * st.session_state.tasas["USDT"])
    elif de == "USD" and a == "ARS":
        resultado = monto_conv * st.session_state.tasas["ARS"]
    elif de == "ARS" and a == "USD":
        resultado = monto_conv / st.session_state.tasas["ARS"]
    elif de == "USDT" and a == "ARS":
        resultado = monto_conv * st.session_state.tasas["ARS"]
    elif de == "ARS" and a == "USDT":
        resultado = monto_conv / st.session_state.tasas["ARS"]
    elif de == "EUR" and a == "USDT":
        resultado = monto_conv * st.session_state.tasas["USDT"]
    elif de == "USDT" and a == "EUR":
        resultado = monto_conv / st.session_state.tasas["USDT"]
    else:
        resultado = monto_conv

    st.write(f"**{monto_conv:,.2f} {de} = {resultado:,.2f} {a}**")

# --- EXPORTAR ---
if st.button("Exportar datos"):
    st.download_button("Descargar JSON", json.dumps(st.session_state.gastos, indent=2), "gastos.json")
