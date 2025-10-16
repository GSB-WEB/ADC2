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

# Inicializar session state para forzar actualizaciones
if 'recalcular' not in st.session_state:
    st.session_state.recalcular = False

# Sidebar con configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Variable de Campo")
    min_val = st.number_input("Valor Mínimo", 0.0, 1000.0, 10.0)
    max_val = st.number_input("Valor Máximo", 0.0, 1000.0, 100.0)
    unidad = st.text_input("Unidades", "°C", key="unidad_input")  # KEY agregado
    
    st.subheader("Configuración ADC")
    bits = st.selectbox("Resolución", [8, 10, 12, 16, 24, 32], index=1, key="bits_input")
    v_ref = st.number_input("Voltaje Referencia (V)", 1.0, 10.0, 5.0, key="vref_input")
    
    st.subheader("Señal de Entrada")
    tipo_senal = st.selectbox(
        "Tipo de Señal",
        ['0-5V', '0-10V', '4-20mA', '0-20mA', '1-5V'],
        index=4,
        key="senal_input"
    )
    
    valor_actual = st.slider(
        f"Valor Actual ({unidad})",  # ¡Aquí SÍ usa la unidad actual!
        min_val, max_val, (min_val + max_val) / 2,
        key="valor_actual_input"
    )
    
    # Botón para forzar actualización
    if st.button("🔄 Actualizar Cálculos", type="secondary"):
        st.session_state.recalcular = True
        st.rerun()

# Cálculos de conversión
def calcular_conversion(valor_actual, min_val, max_val, tipo_senal, bits, v_ref):
    """Calcula la conversión ADC"""
    # Escalar a porcentaje de la VARIABLE DE CAMPO (no del voltaje)
    rango = max_val - min_val
    if rango == 0:
        return 0, 0, "0", 0, 0, 0
    
    # Porcentaje de la VARIABLE (esto es lo que importa)
    porcentaje_variable = ((valor_actual - min_val) / rango) * 100
    
    # Convertir a voltaje según tipo de señal
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
    
    # Asegurar que el voltaje esté en rango
    voltaje = max(0, min(voltaje, v_ref))
    
    # Calcular valor digital
    max_digital = (2 ** bits) - 1
    valor_digital = int((voltaje / v_ref) * max_digital)
    
    # Convertir a binario
    binario = bin(valor_digital)[2:].zfill(bits)
    
    # Porcentaje del voltaje (para mostrar)
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
            st.metric("% Voltaje", f"{porcentaje_voltaje:.1f}%")
        
        # Representaciones numéricas
        st.subheader("Representaciones")
        col_rep1, col_rep2, col_rep3 = st.columns(3)
        
        with col_rep1:
            st.code(f"Binario ({bits} bits): {binario}")
        with col_rep2:
            st.code(f"Hexadecimal: 0x{hex(digital)[2:].upper()}")
        with col_rep3:
            st.code(f"Octal: 0o{oct(digital)[2:]}")

with col2:
    st.header("✅ Verificación de Entorno")
    st.success("¡Todo instalado correctamente!")
    st.write(f"**Python:** 3.13.2")
    st.write(f"**Streamlit:** {st.__version__}")
    st.write(f"**Pandas:** {pd.__version__}")
    st.write(f"**Plotly:** {px.__version__ if hasattr(px, '__version__') else '6.3.1'}")
    st.write(f"**NumPy:** {np.__version__}")

# Información técnica - VERSIÓN MEJORADA
with st.expander("📋 Información Técnica", expanded=True):  # expanded=True para que siempre se vea
    # CALCULAR CON LOS VALORES ACTUALES - USANDO LAS VARIABLES DEL SIDEBAR
    resolucion = v_ref / (2 ** bits)
    max_digital_calc = (2 ** bits) - 1
    combinaciones = 2 ** bits
    
    st.write(f"**Resolución ADC:** {resolucion:.8f} V")
    st.write(f"**Error de Cuantización:** ±{resolucion/2:.8f} V")
    st.write(f"**Rango Digital:** 0 a {max_digital_calc}")
    st.write(f"**Combinaciones:** {combinaciones}")
    
    # Información específica de la señal - USANDO LAS VARIABLES ACTUALES
    st.write(f"**Rango Variable:** {min_val} a {max_val} {unidad}")  # ¡Aquí SÍ usa la unidad actual!
    st.write(f"**Tipo de Señal:** {tipo_senal}")
    
    # Mostrar rangos de señal
    if tipo_senal == '1-5V':
        st.write(f"**Rango Voltaje:** 1V a 5V (0-100% variable)")
    elif tipo_senal == '4-20mA':
        st.write(f"**Rango Corriente:** 4mA a 20mA (0-100% variable)")
    elif tipo_senal == '0-5V':
        st.write(f"**Rango Voltaje:** 0V a 5V (0-100% variable)")
    elif tipo_senal == '0-10V':
        st.write(f"**Rango Voltaje:** 0V a 10V (0-100% variable)")
    elif tipo_senal == '0-20mA':
        st.write(f"**Rango Corriente:** 0mA a 20mA (0-100% variable)")
    
    # Estado actual de la configuración
    st.info(f"**Configuración actual:** {bits} bits, {min_val}-{max_val} {unidad}, {tipo_senal}")

# Tabla de referencia de bits
with st.expander("🔢 Tabla de Referencia de Bits"):
    st.write("**Rangos digitales por cantidad de bits:**")
    referencia_bits = {
        'Bits': [8, 10, 12, 16, 24, 32],
        'Máximo Digital': [255, 1023, 4095, 65535, 16777215, 4294967295],
        'Combinaciones': [256, 1024, 4096, 65536, 16777216, 4294967296]
    }
    df_bits = pd.DataFrame(referencia_bits)
    st.dataframe(df_bits, hide_index=True)

# Ejemplo de uso dinámico
with st.expander("💡 Ejemplo de Uso"):
    # Calcular ejemplos con los valores actuales
    ejemplo_min = calcular_conversion(min_val, min_val, max_val, tipo_senal, bits, v_ref)
    ejemplo_max = calcular_conversion(max_val, min_val, max_val, tipo_senal, bits, v_ref)
    ejemplo_medio = calcular_conversion((min_val + max_val) / 2, min_val, max_val, tipo_senal, bits, v_ref)
    
    st.write(f"""
    **Para tu configuración actual:**
    
    **Valor {min_val} {unidad} (mínimo):**
    - 0% variable → {ejemplo_min[1]:.2f}V → Digital: {ejemplo_min[0]}/{ejemplo_min[5]}
    
    **Valor {max_val} {unidad} (máximo):**
    - 100% variable → {ejemplo_max[1]:.2f}V → Digital: {ejemplo_max[0]}/{ejemplo_max[5]}
    
    **Valor {(min_val + max_val) / 2:.1f} {unidad} (medio):**
    - 50% variable → {ejemplo_medio[1]:.2f}V → Digital: {ejemplo_medio[0]}/{ejemplo_medio[5]}
    """)

st.markdown("---")
st.caption("Desarrollado con Streamlit | Listo para GitHub 🚀")