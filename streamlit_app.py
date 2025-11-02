import streamlit as st
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import json

st.set_page_config(page_title="AhorroSmart", layout="wide")
st.title("AhorroSmart - Control de Gastos y Ahorro")

# Inicializar datos
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
    st.session_state.tasas = {"EUR": 1.0, "ARS": 1100.0, "USD": 0.92}

# Actualizar tasas
def actualizar_tasas():
    try:
        data = requests.get("https://api.exchangerate-api.com/v4/latest/EUR").json()
        st.session_state.tasas["ARS"] = data['rates']['ARS']
        st.session_state.tasas["USD"] = data['rates']['USD']
        st.success("Tasas actualizadas")
    except:
        st.warning("Sin internet - usando tasas simuladas")

# Sidebar
with st.sidebar:
    st.header("Configuración")
    st.session_state.ingresos["sueldo"] = st.number_input("Sueldo (€)", value=1800.0)
    st.session_state.ingresos["freelance"] = st.number_input("Freelance (€)", value=250.0)
    if st.button("Actualizar tasas"):
        actualizar_tasas()

# Cálculos
total_ingresos = sum(st.session_state.ingresos.values())
ahorro_objetivo = 150
presupuesto = total_ingresos - ahorro_objetivo

col1, col2, col3 = st.columns(3)
col1.metric("Ingresos", f"€{total_ingresos:,.2f}")
col2.metric("Ahorro Objetivo", f"€{ahorro_objetivo}")
col3.metric("Para Gastos", f"€{presupuesto:,.2f}")

# Agregar gasto
st.subheader("Agregar Gasto")
c1, c2 = st.columns(2)
with c1:
    monto = st.number_input("Monto", min_value=0.01)
    moneda = st.selectbox("Moneda", ["EUR", "ARS", "USD"])
with c2:
    cat = st.selectbox("Categoría", list(st.session_state.categorias.keys()))
    sub = st.selectbox("Subcategoría", st.session_state.categorias[cat])
desc = st.text_input("Descripción")

if st.button("Guardar Gasto"):
    tasa = st.session_state.tasas[moneda]
    monto_eur = monto / tasa if moneda != "EUR" else monto
    st.session_state.gastos.append({
        "monto": monto, "moneda": moneda, "monto_eur": monto_eur,
        "cat": cat, "sub": sub, "desc": desc,
        "fecha": datetime.now().strftime("%d/%m/%Y")
    })
    st.success(f"Guardado: {monto} {moneda} → €{monto_eur:.2f}")

# Análisis
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

# Western Union
st.subheader("Convertir Pesos a Euros")
ars = st.number_input("Pesos Argentinos (ARS)", min_value=0.0)
if ars > 0:
    eur = ars / st.session_state.tasas["ARS"]
    st.write(f"**≈ €{eur:.2f}** (1€ = {st.session_state.tasas['ARS']:,.0f} ARS)")
    st.markdown("[Ver en Western Union](https://www.westernunion.com)")

# Exportar
if st.button("Exportar datos"):
    st.download_button("Descargar JSON", json.dumps(st.session_state.gastos, indent=2), "gastos.json")
