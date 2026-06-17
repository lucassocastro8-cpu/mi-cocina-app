import streamlit as st
import pandas as pd
import requests
import json

# Configuración visual de la aplicación
st.set_page_config(page_title="Nuestra Cocina Sincronizada", page_icon="🍳", layout="centered")

# ==========================================
# 🗺️ SISTEMA DE EMPAREJAMIENTO POR URL
# ==========================================
# Revisamos si ya existe un código de cocina en el link del navegador
if "id" in st.query_params:
    bucket_id = st.query_params["id"]
else:
    bucket_id = None

# Si es la primera vez absoluta y no hay ID, generamos uno oficial en la nube
if not bucket_id:
    st.info("🚀 Creando tu espacio de cocina seguro y permanente en la nube...")
    try:
        # Solicitamos un identificador real y libre a kvdb.io
        crear_bucket = requests.post("https://kvdb.io/new", timeout=5)
        if crear_bucket.status_code == 200:
            bucket_id = crear_bucket.text.strip()
            # Guardamos el ID en la URL del navegador
            st.query_params["id"] = bucket_id
            
            # Valores iniciales de muestra por única vez
            alacena_inicial = {"Arroz": 1000, "Fideos": 500, "Puré de Tomate": 2, "Cebolla": 4, "Carne Picada": 500}
            recetas_iniciales = {
                "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
                "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
            }
            # Subir configuración inicial
            requests.put(f"https://kvdb.io/{bucket_id}/alacena", data=json.dumps(alacena_inicial))
            requests.put(f"https://kvdb.io/{bucket_id}/recetas", data=json.dumps(recetas_iniciales))
            st.success("¡Cocina en la nube activada!")
            st.rerun()
    except Exception as e:
        st.error(f"Error al inicializar la base de datos: {e}")
        st.stop()

# Definimos las rutas finales con tu ID único guardado en el link
URL_ALACENA = f"https://kvdb.io/{bucket_id}/alacena"
URL_RECETAS = f"https://kvdb.io/{bucket_id}/recetas"

# --- FUNCIONES DE ALTA FIABILIDAD ---
def cargar_alacena_nube():
    try:
        respuesta = requests.get(URL_ALACENA, timeout=5)
        if respuesta.status_code == 200: return json.loads(respuesta.text)
    except: pass
    return {}

def guardar_alacena_nube(datos):
    try: requests.put(URL_ALACENA, data=json.dumps(datos), timeout=5)
    except: st.error("Error temporal de red al guardar en la alacena.")

def cargar_recetas_nube():
    try:
        respuesta = requests.get(URL_RECETAS, timeout=5)
        if respuesta.status_code == 200: return json.loads(respuesta.text)
    except: pass
    return {}

def guardar_recetas_nube(datos):
    try: requests.put(URL_RECETAS, data=json.dumps(datos), timeout=5)
    except: st.error("Error temporal de red al guardar las recetas.")

# --- CONTROL DE SESIÓN AUTOMÁTICO (F5 PROTECTION) ---
if "alacena_data" not in st.session_state or st.sidebar.button("🔄 Forzar Sincronización"):
    st.session_state.alacena_data = cargar_alacena_nube()

if "recetas_data" not in st.session_state:
    st.session_state.recetas_data = cargar_recetas_nube()

# Formatear datos de la alacena
df_alacena = pd.DataFrame(list(st.session_state.alacena_data.items()), columns=["Ingrediente", "Cantidad"])

# Títulos principales
st.title("🍳 Nuestra Cocina Sincronizada")

# Cuadro informativo de emparejamiento para el usuario
with st.expander("🔗 LINK COMPARTIDO PARA TU NOVIA (Toca aquí)"):
    st.write("Para que tu novia vea exactamente tus mismos ingredientes y recetas, compartile el enlace completo que aparece arriba en tu navegador. Tiene que incluir el código del final.")
    st.code(f"https://share.streamlit.io/ (Tu enlace de la app) /?id={bucket_id}")

# Pestañas de la aplicación
tab_cocina, tab_recetas, tab_alacena = st.tabs(["🍳 Cocinar Hoy", "📖 Recetas Compartidas", "📦 Alacena Compartida"])

# ==========================================
# 1. PESTAÑA: COCINA
# ==========================================
with tab_cocina:
    st.header("🍳 ¿Qué preparamos para comer?")
    opciones_recetas = sorted(list(st.session_state.recetas_data.keys()))
    
    if opciones_recetas:
        receta_elegida = st.selectbox("Elegir menú:", opciones_recetas)
        ingredientes_necesarios = st.session_state.recetas_data[receta_elegida]
        
        st.subheader("📋 Verificación de Stock")
        puede_cocinar = True
        
        for ing, cant_req in ingredientes_necesarios.items():
            cant_disponible = st.session_state.alacena_data.get(ing, 0)
            if cant_disponible >= cant_req:
                st.write(f"✅ **{ing}**: Necesitas {cant_req} | Tienes {cant_disponible}")
            else:
                st.write(f"❌ **{ing}**: Necesitas {cant_req} | ¡Solo tienes {cant_disponible}! ⚠️")
                puede_cocinar = False
                
        st.write("---")
        if puede_cocinar:
            if st.button("🍽️ ¡Hecho! Cocinado", type="primary"):
                for ing, cant_req in ingredientes_necesarios.items():
                    st.session_state.alacena_data[ing] -= cant_req
                guardar_alacena_nube(st.session_state.alacena_data)
                st.balloons()
                st.success("¡Buen provecho! El stock se descontó de la nube para ambos.")
                st.rerun()
        else:
            st.error("Faltan ingredientes en la Alacena para este plato.")
    else:
        st.info("Crea un plato en la pestaña 'Recetas Compartidas' para empezar.")

# ==========================================
# 2. PESTAÑA: RECETAS
# ==========================================
with tab_recetas:
    st.header("📖 Recetario en la Nube")
    
    for nombre_r, ing_r in sorted(st.session_state.recetas_data.items()):
        with st.expander(f"🍴 {nombre_r}"):
            for ing, cant in ing_r.items():
                st.write(f"- {ing}: {cant}")
            if st.button(f"🗑️ Eliminar {nombre_r}", key=f"del_{nombre_r}"):
                del st.session_state.recetas_data[nombre_r]
                guardar_recetas_nube(st.session_state.recetas_data)
                st.rerun()

    st.write("---")
    st.subheader("➕ Crear Nueva Receta")
    nombre_nueva_receta = st.text_input("Nombre del plato nuevo:").strip().title()
    ingredientes_disponibles = sorted(list(st.session_state.alacena_data.keys()))
    ings_elegidos = st.multiselect("Selecciona qué ingredientes lleva:", ingredientes_disponibles)
    
    cantidades_ing = {}
    if ings_elegidos:
        for ing in ings_elegidos:
            cantidades_ing[ing] = st.number_input(f"Cantidad de '{ing}':", min_value=1, value=100, key=f"cant_{ing}")
            
    if st.button("💾 Guardar Plato en el Recetario"):
        if nombre_nueva_receta and cantidades_ing:
            st.session_state.recetas_data[nombre_nueva_receta] = cantidades_ing
            guardar_recetas_nube(st.session_state.recetas_data)
            st.success("¡Receta guardada!")
            st.rerun()

# ==========================================
# 3. PESTAÑA: ALACENA
# ==========================================
with tab_alacena:
    st.header("📦 Inventario en la Nube")
    st.dataframe(df_alacena, use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("➕ Agregar o Reponer Alimentos")
    with st.form("form_alacena"):
        nuevo_ing = st.text_input("Nombre del alimento:").strip().title()
        nueva_cant = st.number_input("Cantidad a sumar:", min_value=1, step=1)
        if st.form_submit_button("Actualizar Alacena") and nuevo_ing:
            if nuevo_ing in st.session_state.alacena_data:
                st.session_state.alacena_data[nuevo_ing] += nueva_cant
            else:
                st.session_state.alacena_data[nuevo_ing] = nueva_cant
            guardar_alacena_nube(st.session_state.alacena_data)
            st.rerun()
