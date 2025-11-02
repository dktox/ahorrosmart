import streamlit as st
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import json
import pandas as pd
from io import BytesIO
import base64
import pytz
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="AhorroSmart", layout="wide")
st.title("AhorroSmart - Gastos + Cotizaciones + Relojes Mundiales")

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

# --- FUNCIÓN RELOJES ---
def mostrar_relojes():
    st.subheader("🕐 Relojes Mundiales (Actualizados en vivo)")
    col1, col2, col3 = st.columns(3)
    
    tz_ny = pytz.timezone("America/New_York")
    tz_arg = pytz.timezone("America/Argentina/Buenos_Aires")
    tz_esp = pytz.timezone("Europe/Madrid")
    
    now_ny = datetime.now(tz_ny).strftime("%H:%M:%S")
    now_arg = datetime.now(tz_arg).strftime("%H:%M:%S")
    now_esp = datetime.now(tz_esp).strftime("%H:%M:%S")
    
    with col1:
        st.metric("🇺🇸 Nueva York", now_ny)
    with col2:
        st.metric("🇦🇷 Argentina", now_arg)
    with col3:
        st.metric("🇪🇸 España", now_esp)
    
    # Auto-refrescar cada 1 segundo
    time.sleep(1)
    st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Configuración")
    st.session_state.ingresos["sueldo"] = st.number_input("Sueldo (€)", value=1800.0)
    st.session_state.ingresos["freelance"] = st.number_input("Freelance (€)", value=250.0)
    
    st.subheader("Agregar Categoría")
    nueva_cat = st.text_input("Nombre")
    nuevas_sub = st.text_area("Subcategorías (una por línea)").splitlines()
    if st.button("Agregar") and nueva_cat:
        st.session_state.categorias[nueva_cat] = [s.strip() for s in nuevas_sub if s.strip()]
        st.success(f"Agregada: {nueva_cat}")

    if st.button("Actualizar cotizaciones"):
        obtener_cotizaciones()

# --- RELOJES EN VIVO ---
mostrar_relojes()

# --- COTIZACIONES ---
st.subheader("Cotizaciones")
if st.button("Forzar actualización"):
    obtener_cotizaciones()

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

# --- GRÁFICO DE BARRAS ---
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

    # GRÁFICO DE BARRAS
    cats = {}
    for g in st.session_state.gastos:
        cats[g["cat"]] = cats.get(g["cat"], 0) + g["monto_eur"]
    
    if cats:
        fig, ax = plt.subplots(figsize=(10, 6))
        categorias = list(cats.keys())
        valores = list(cats.values())
        bars = ax.bar(categorias, valores, color='skyblue', edgecolor='navy')
        ax.set_title("Gastos por Categoría (€)", fontsize=16, fontweight='bold')
        ax.set_ylabel("Monto en Euros (€)")
        ax.set_xlabel("Categoría")
        plt.xticks(rotation=45, ha='right')
        
        # Añadir valores encima de las barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(valores)*0.01,
                    f'€{height:,.0f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        st.pyplot(fig)

# --- EXPORTAR A EXCEL ---
if st.session_state.gastos:
    df = pd.DataFrame(st.session_state.gastos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Gastos')
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="gastos_ahorrosmart.xlsx">📥 Descargar Excel</a>'
    st.markdown(href, unsafe_allow_html=True)
