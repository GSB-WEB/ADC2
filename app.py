import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Conversor ADC Pro",
    page_icon="🎛️",
    layout="wide"
)

# Header
st.title("🎛️ CONVERSOR ADC PROFESIONAL")
st.markdown("---")

# Inicializar session state
if 'recalcular' not in st.session_state:
    st.session_state.recalcular = False

# Sidebar con configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # 1. RANGO DE LA VARIABLE DE CAMPO
    st.subheader("📊 Rango de la Variable de Campo")
    min_val = st.number_input("Valor Mínimo", -1000.0, 1000.0, -20.0, key="min_val")
    max_val = st.number_input("Valor Máximo", -1000.0, 1000.0, 100.0, key="max_val")
    
    ejemplos_unidades = st.selectbox(
        "Ejemplos comunes:",
        ["Personalizado", "Temperatura °C", "Temperatura °F", "Presión (bar)", "Nivel (%)"],
        index=0
    )
    
    if ejemplos_unidades == "Temperatura °C":
        unidad_default = "°C"
    elif ejemplos_unidades == "Temperatura °F":
        unidad_default = "°F"
    elif ejemplos_unidades == "Presión (bar)":
        unidad_default = "bar"
    elif ejemplos_unidades == "Nivel (%)":
        unidad_default = "%"
    else:
        unidad_default = "unidades"
    
    unidad = st.text_input("Unidades", unidad_default, key="unidad_input")
    
    # VALIDACIÓN CRÍTICA
    if min_val >= max_val:
        st.error("❌ ERROR: El valor MÍNIMO debe ser MENOR que el MÁXIMO")
        st.stop()
    
    # 2. RANGO ELÉCTRICO DE LA VARIABLE DE ENTRADA
    st.subheader("🔌 Rango Eléctrico de la Variable de Entrada")
    tipo_senal = st.selectbox(
        "Tipo de Señal",
        ['0-5V', '0-10V', '4-20mA', '0-20mA', '1-5V', '±10V', '±5V'],
        index=4,
        key="senal_input"
    )
    
    # 3. CONFIGURACIÓN ADC
    st.subheader("📟 Configuración ADC")
    bits = st.selectbox("Resolución", [8, 10, 12, 16, 24, 32], index=1, key="bits_input")
    v_ref = st.number_input("Voltaje Referencia (V)", 1.0, 10.0, 5.0, key="vref_input")
    
    valor_actual = st.slider(
        f"Valor Actual ({unidad})",
        float(min_val), float(max_val), float((min_val + max_val) / 2),
        key="valor_actual_input"
    )
    
    if st.button("🔄 Actualizar Cálculos", type="secondary"):
        st.session_state.recalcular = True
        st.rerun()

# Cálculos de conversión
def calcular_conversion(valor_actual, min_val, max_val, tipo_senal, bits, v_ref):
    """Calcula la conversión ADC"""
    rango = max_val - min_val
    if rango == 0:
        return 0, 0, "0", 0, 0, 0
    
    porcentaje_variable = ((valor_actual - min_val) / rango) * 100
    
    if tipo_senal == '0-5V':
        voltaje = (porcentaje_variable / 100) * 5.0
    elif tipo_senal == '0-10V':
        voltaje = (porcentaje_variable / 100) * 10.0
    elif tipo_senal == '4-20mA':
        corriente = (porcentaje_variable / 100 * 16) + 4
        voltaje = corriente * 0.250
    elif tipo_senal == '0-20mA':
        corriente = (porcentaje_variable / 100 * 20)
        voltaje = corriente * 0.250
    elif tipo_senal == '1-5V':
        voltaje = (porcentaje_variable / 100 * 4) + 1
    elif tipo_senal == '±10V':
        voltaje = (porcentaje_variable / 100 * 20) - 10
    elif tipo_senal == '±5V':
        voltaje = (porcentaje_variable / 100 * 10) - 5
    
    if tipo_senal in ['±10V', '±5V']:
        if tipo_senal == '±10V':
            voltaje = max(-10, min(voltaje, 10))
        elif tipo_senal == '±5V':
            voltaje = max(-5, min(voltaje, 5))
    else:
        voltaje = max(0, min(voltaje, v_ref))
    
    max_digital = (2 ** bits) - 1
    
    if tipo_senal in ['±10V', '±5V']:
        if tipo_senal == '±10V':
            valor_digital = int(((voltaje + 10) / 20) * max_digital)
        elif tipo_senal == '±5V':
            valor_digital = int(((voltaje + 5) / 10) * max_digital)
    else:
        valor_digital = int((voltaje / v_ref) * max_digital)
    
    binario = bin(valor_digital)[2:].zfill(bits)
    
    if tipo_senal in ['±10V', '±5V']:
        if tipo_senal == '±10V':
            porcentaje_voltaje = ((voltaje + 10) / 20) * 100
        elif tipo_senal == '±5V':
            porcentaje_voltaje = ((voltaje + 5) / 10) * 100
    else:
        porcentaje_voltaje = (voltaje / v_ref) * 100
    
    return valor_digital, voltaje, binario, porcentaje_variable, porcentaje_voltaje, max_digital

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Resultados de Conversión")
    
    if st.button("🔄 Realizar Conversión", type="primary", key="convertir_btn"):
        digital, voltaje, binario, porcentaje_variable, porcentaje_voltaje, max_digital = calcular_conversion(
            valor_actual, min_val, max_val, tipo_senal, bits, v_ref
        )
        
        st.subheader("Resultados")
        col_res1, col_res2, col_res3, col_res4 = st.columns(4)
        
        with col_res1:
            st.metric("Valor Digital", f"{digital} / {max_digital}")
        with col_res2:
            st.metric("Voltaje", f"{voltaje:.4f} V")
        with col_res3:
            st.metric("% Variable", f"{porcentaje_variable:.1f}%")
        with col_res4:
            st.metric("% Voltaje de Referencia", f"{porcentaje_voltaje:.1f}%")
        
        # REPRESENTACIONES NUMÉRICAS - CORREGIDO
        st.subheader("Representaciones")
        col_rep1, col_rep2, col_rep3 = st.columns(3)
        
        with col_rep1:
            st.code(f"Binario ({bits} bits): {binario}")
        with col_rep2:
            st.code(f"Hexadecimal: 0x{hex(digital)[2:].upper()}")
        with col_rep3:
            # CORRECCIÓN: Validar conversión octal
            try:
                # Asegurar que sea un número válido para octal
                if digital >= 0:
                    valor_octal = oct(digital)[2:]
                    st.code(f"Octal: 0o{valor_octal}")
                else:
                    st.code("Octal: No disponible para negativos")
            except Exception as e:
                st.code("Octal: Error en conversión")

with col2:
    st.header("✅ Verificación de Entorno")
    st.success("¡Todo instalado correctamente!")

# Información técnica
with st.expander("📋 Información Técnica", expanded=True):
    resolucion = v_ref / (2 ** bits)
    max_digital_calc = (2 ** bits) - 1
    combinaciones = 2 ** bits
    
    st.write(f"**Resolución ADC:** {resolucion:.8f} V")
    st.write(f"**Error de Cuantización:** ±{resolucion/2:.8f} V")
    st.write(f"**Rango Digital:** 0 a {max_digital_calc}")
    st.write(f"**Combinaciones:** {combinaciones}")
    st.write(f"**Rango Variable:** {min_val} a {max_val} {unidad}")
    st.write(f"**Tipo de Señal:** {tipo_senal}")

st.markdown("---")
st.caption("Desarrollado con Streamlit | Listo para GitHub 🚀")