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

# Sidebar con configuración - AHORA CON VALORES NEGATIVOS
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # 1. RANGO DE LA VARIABLE DE CAMPO - AHORA CON NEGATIVOS
    st.subheader("📊 Rango de la Variable de Campo")
    
    # Configurar límites más amplios que permitan negativos
    min_val = st.number_input("Valor Mínimo", -1000.0, 1000.0, -20.0, key="min_val")  # CAMBIADO: -1000.0
    max_val = st.number_input("Valor Máximo", -1000.0, 1000.0, 100.0, key="max_val")  # CAMBIADO: -1000.0
    
    # Ejemplos comunes para facilitar al usuario
    ejemplos_unidades = st.selectbox(
        "Ejemplos comunes:",
        ["Personalizado", "Temperatura °C", "Temperatura °F", "Presión (bar)", "Nivel (%)"],
        index=0
    )
    
    # Auto-completar según ejemplo seleccionado
    if ejemplos_unidades == "Temperatura °C":
        unidad_default = "°C"
        min_default = -20.0
        max_default = 100.0
    elif ejemplos_unidades == "Temperatura °F":
        unidad_default = "°F" 
        min_default = -4.0
        max_default = 212.0
    elif ejemplos_unidades == "Presión (bar)":
        unidad_default = "bar"
        min_default = 0.0
        max_default = 10.0
    elif ejemplos_unidades == "Nivel (%)":
        unidad_default = "%"
        min_default = 0.0
        max_default = 100.0
    else:
        unidad_default = "unidades"
        min_default = min_val
        max_default = max_val
    
    unidad = st.text_input("Unidades", unidad_default, key="unidad_input")
    
    # VALIDACIÓN CRÍTICA - Evitar error del slider
    if min_val >= max_val:
        st.error("❌ ERROR: El valor MÍNIMO debe ser MENOR que el MÁXIMO")
        st.stop()  # Detener la ejecución hasta que se corrija
    
    # 2. RANGO ELÉCTRICO DE LA VARIABLE DE ENTRADA
    st.subheader("🔌 Rango Eléctrico de la Variable de Entrada")
    tipo_senal = st.selectbox(
        "Tipo de Señal",
        ['0-5V', '0-10V', '4-20mA', '0-20mA', '1-5V', '±10V', '±5V'],  # AGREGADAS señales bipolar
        index=4,
        key="senal_input"
    )
    
    # 3. CONFIGURACIÓN ADC
    st.subheader("📟 Configuración ADC")
    bits = st.selectbox("Resolución", [8, 10, 12, 16, 24, 32], index=1, key="bits_input")
    v_ref = st.number_input("Voltaje Referencia (V)", 1.0, 10.0, 5.0, key="vref_input")
    
    # Slider con valores válidos - AHORA SOPORTA NEGATIVOS
    valor_actual = st.slider(
        f"Valor Actual ({unidad})",
        float(min_val), float(max_val), float((min_val + max_val) / 2),
        key="valor_actual_input"
    )
    
    # Botón para forzar actualización
    if st.button("🔄 Actualizar Cálculos", type="secondary"):
        st.session_state.recalcular = True
        st.rerun()

# Cálculos de conversión - ACTUALIZADO PARA SEÑALES BIPOLARES
def calcular_conversion(valor_actual, min_val, max_val, tipo_senal, bits, v_ref):
    """Calcula la conversión ADC - AHORA CON SOPORTE PARA NEGATIVOS"""
    # Escalar a porcentaje de la VARIABLE DE CAMPO
    rango = max_val - min_val
    if rango == 0:
        return 0, 0, "0", 0, 0, 0
    
    # Porcentaje de la VARIABLE (esto es lo que importa)
    porcentaje_variable = ((valor_actual - min_val) / rango) * 100
    
    # Convertir a voltaje según tipo de señal - AGREGADAS SEÑALES BIPOLARES
    if tipo_senal == '0-5V':
        voltaje = (porcentaje_variable / 100) * 5.0
    elif tipo_senal == '0-10V':
        voltaje = (porcentaje_variable / 100) * 10.0
    elif tipo_senal == '4-20mA':
        # 4-20mA: 0% variable = 4mA, 100% variable = 20mA
        corriente = (porcentaje_variable / 100 * 16) + 4
        voltaje = corriente * 0.250  # 250Ω resistor
    elif tipo_senal == '0-20mA':
        corriente = (porcentaje_variable / 100 * 20)
        voltaje = corriente * 0.250  # 250Ω resistor
    elif tipo_senal == '1-5V':
        # Para 1-5V: 0% variable = 1V, 100% variable = 5V
        voltaje = (porcentaje_variable / 100 * 4) + 1
    elif tipo_senal == '±10V':
        # Para ±10V: 0% variable = -10V, 100% variable = +10V
        voltaje = (porcentaje_variable / 100 * 20) - 10
    elif tipo_senal == '±5V':
        # Para ±5V: 0% variable = -5V, 100% variable = +5V
        voltaje = (porcentaje_variable / 100 * 10) - 5
    
    # Asegurar que el voltaje esté en rango según el tipo de señal
    if tipo_senal in ['±10V', '±5V']:
        # Para señales bipolares, el voltaje puede ser negativo
        if tipo_senal == '±10V':
            voltaje = max(-10, min(voltaje, 10))
        elif tipo_senal == '±5V':
            voltaje = max(-5, min(voltaje, 5))
    else:
        # Para señales unipolares, voltaje debe ser positivo
        voltaje = max(0, min(voltaje, v_ref))
    
    # Calcular valor digital - CONSIDERANDO VOLTAJES NEGATIVOS
    max_digital = (2 ** bits) - 1
    
    if tipo_senal in ['±10V', '±5V']:
        # Para señales bipolares: voltaje negativo = digital bajo, positivo = digital alto
        if tipo_senal == '±10V':
            # Mapear -10V a 0, +10V a max_digital
            valor_digital = int(((voltaje + 10) / 20) * max_digital)
        elif tipo_senal == '±5V':
            # Mapear -5V a 0, +5V a max_digital
            valor_digital = int(((voltaje + 5) / 10) * max_digital)
    else:
        # Para señales unipolares
        valor_digital = int((voltaje / v_ref) * max_digital)
    
    # Convertir a binario
    binario = bin(valor_digital)[2:].zfill(bits)
    
    # Porcentaje del voltaje (para mostrar)
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
        
        # Mostrar resultados
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
        
        # Representaciones numéricas
        st.subheader("Representaciones")
        col_rep1, col_rep2, col_rep3 = st.columns(3)
        
        with col_rep1:
            st.code(f"Binario ({bits} bits): {binario}")
        with col_rep2:
            st.code(f"Hexadecimal: 0x{hex(digital)[2:].upper()}")
        with col_rep3:
            st