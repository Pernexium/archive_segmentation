import math
import pandas as pd
from io import BytesIO
import streamlit as st
from datetime import datetime

def normalize_text(text):
    if isinstance(text, str):
        # Reemplazar caracteres específicos
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'ñ': 'n', 'Ñ': 'N',
            'ü': 'u', 'Ü': 'U'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
    return text

# Aplicar la función de normalización a todo el DataFrame
def normalize_dataframe(df):
    return df.applymap(normalize_text)

# Paso 1: Seleccione la campaña
st.title("Segmentador de Archivos")
st.subheader("Paso 1: Seleccione la campaña")
campania = st.selectbox("Seleccione la campaña", ["BanCoppel", "Monte de Piedad"])
st.markdown("---")

if campania:
    # Paso 2: Verifique los agentes de la campaña
    st.subheader("Paso 2: Verifique los agentes de la campaña")
    if campania == "BanCoppel":
        nombres = ["Natalia Vega", "Patricia Salazar", "Arturo Cuevas", "Itzel Valencia", "Luca Oseguera", "Nery Espiritu", "Manuel Avila"]
    elif campania == "Monte de Piedad":
        nombres = ["Amairani", "Ana Karen", "Tania Patricia", "Goretti Xaire", "Adriana Palacios", "Jose Rangel"]

    agentes_seleccionados = st.multiselect("Seleccione los agentes", nombres)
    num_agentes_seleccionados = len(agentes_seleccionados)

    st.write(f"Cantidad de agentes seleccionados: {num_agentes_seleccionados}")
    st.markdown("---")


    # Paso 3: Cargue un archivo CSV o Excel
    st.subheader("Paso 3: Cargue un archivo CSV o Excel")
    st.write("Por favor, carga un archivo CSV o Excel para visualizar los datos.")
    uploaded_file = st.file_uploader("Cargar archivo", type = ["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file, encoding = 'latin-1')
                except Exception as e_utf8:
                    try:
                        df = pd.read_csv(uploaded_file, encoding = 'utf-8')
                    except Exception as e_latin1:
                        st.error(f"Error al leer el archivo CSV: {e_utf8} / {e_latin1}")
                        st.stop()
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)

            if df.empty or df.columns.empty:
                st.error("El archivo cargado está vacío o no tiene columnas.")
                st.stop()

            st.success("¡Archivo cargado exitosamente!")
            st.markdown("---")
            
            df = normalize_dataframe(df)


            # Paso 4: Visualice los datos del archivo
            st.subheader("Paso 4: Visualice los datos del archivo")
            num_filas, num_columnas = df.shape
            st.write(f"El archivo tiene {num_filas} filas (sin contar el encabezado) y {num_columnas} columnas.")

            st.write("Vista previa de los datos:")
            st.write(df.head())
            st.markdown("---")
 
 
            # Paso 5: Segmente los datos
            st.subheader("Paso 5: Segmente los datos")

            st.write("Seleccione una de las opciones a continuación para segmentar los datos:")

            st.write("- **Distribución con Tope:** Este botón segmenta el archivo asegurando que cada segmento tenga un máximo de filas especificado.")
            tope_filas = st.number_input("Ingrese el tope máximo de filas por segmento (dar Enter para aplicar):", min_value = 1, step = 50, value = 1000)
            
            st.markdown("""
    <style>
    .stButton button {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """, unsafe_allow_html = True)

            if st.button("Distribución con Tope"):
                segmentos = []
                current_agent_idx = 0
                for start in range(0, num_filas, tope_filas):
                    end = min(start + tope_filas, num_filas)
                    segmentos.append((agentes_seleccionados[current_agent_idx], df.iloc[start:end]))
                    current_agent_idx = (current_agent_idx + 1) % num_agentes_seleccionados

                fecha_actual = datetime.now().strftime("%Y_%m_%d")
                campania_formateada = campania.replace(" ", "_").lower()

                st.session_state.segmentos = []
                for idx, (agente, segmento) in enumerate(segmentos):
                    num_filas_segmento, num_columnas_segmento = segmento.shape
                    agente_formateado = agente.replace(" ", "_").lower()
                    nombre_archivo = f"{fecha_actual}_detonaciones_{campania_formateada}_{agente_formateado}_s{idx + 1}"
                    st.write(f"**Segmento {idx + 1} para {agente} con {num_filas_segmento} filas y {num_columnas_segmento} columnas**")
                    # st.write(segmento.head())

                    csv = segmento.to_csv(index = False)
                    st.session_state.segmentos.append((f"Descargar segmento {idx + 1} para {agente}", csv, f"{nombre_archivo}.csv"))

                st.markdown("---")

            st.write("- **Distribución Equitativa:** Este botón segmenta el archivo en partes iguales entre los agentes seleccionados.")

            if st.button("Distribución Equitativa"):
                filas_por_segmento = math.ceil(num_filas / num_agentes_seleccionados)
                segmentos = [df.iloc[i*filas_por_segmento:(i+1)*filas_por_segmento] for i in range(num_agentes_seleccionados)]
                
                fecha_actual = datetime.now().strftime("%Y_%m_%d")
                campania_formateada = campania.replace(" ", "_").lower()

                st.session_state.segmentos = []
                for idx, segmento in enumerate(segmentos):
                    num_filas_segmento, num_columnas_segmento = segmento.shape
                    agente = agentes_seleccionados[idx].replace(" ", "_").lower()
                    nombre_archivo = f"{fecha_actual}_detonaciones_{campania_formateada}_{agente}_s{idx + 1}"
                    st.write(f"**Segmento {idx + 1} para {agentes_seleccionados[idx]} con {num_filas_segmento} filas y {num_columnas_segmento} columnas**")
                    # st.write(segmento.head())

                    csv = segmento.to_csv(index = False)
                    st.session_state.segmentos.append((f"Descargar segmento {idx + 1} para {agentes_seleccionados[idx]}", csv, f"{nombre_archivo}.csv"))


        except Exception as e:
            st.error(f"Error al cargar el archivo: {e}")
    else:
        st.info("Esperando a que cargues un archivo...")
    st.markdown("---")    


    # Paso 6: Descargue los segmentos
    st.subheader("Paso 6: Descargue los segmentos")
    st.write("Descargue los segmentos generados en el paso 5.")
    if "segmentos" in st.session_state and st.session_state.segmentos:
        for label, csv, file_name in st.session_state.segmentos:
            st.download_button(
                label = label,
                data = csv,
                file_name = file_name,
                mime = 'text/csv'
            )
    else:
        st.info("Primero debes cargar un archivo y segmentarlo.")
