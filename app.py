import streamlit as st
import pandas as pd
import requests
import json

# Configuración visual de la aplicación
st.set_page_config(page_title="Nuestra Cocina Sincronizada", page_icon="🍳", layout="centered")

# --- BASE DE DATOS EN LA NUBE PRO Y GRATUITA (KVDB) ---
# Usamos un contenedor único y oculto para que nadie les pise los datos
ID_CONTENEDOR = "lucas_bren_cocina_db_2026_final"
URL_ALACENA = f"https://kvdb.io/{ID_CONTENEDOR}/alacena"
URL_RECETAS = f"https://kvdb.io/{ID_CONTENEDOR}/recetas"

st.title("🍳 Nuestra Cocina Sincronizada")
st.write("¡Inventario y recetario persistentes en la nube! No se borra al recargar.")

# --- FUNCIONES DE CONTROL SEGURO PARA LA ALACENA ---
def cargar_alacena_nube():
    try:
        respuesta = requests.get(URL_ALACENA, timeout=5)
        if respuesta.status_code == 200:
            return json.loads(respuesta.text)
    except:
        pass
    # Solo carga esto si la base de datos está totalmente vacía por primera vez
    valores_fabrica = {"Arroz": 1000, "Fideos": 500, "Puré de Tomate": 2, "Cebolla": 4, "Carne Picada": 500}
    guardar_alacena_nube(valores_fabrica)
    return valores_fabrica

def guardar_alacena_nube(datos):
    try:
        requests.put(URL_ALACENA, data=json.dumps(datos), timeout=5)
    except Exception as e:
        st.error(f"Error al guardar alacena en la nube: {e}")

# --- FUNCIONES DE CONTROL SEGURO PARA LAS RECETAS ---
def cargar_recetas_nube():
    try:
        respuesta = requests.get(URL_RECETAS, timeout=5)
        if respuesta.status_code == 200:
            return json.loads(respuesta.text)
    except:
        pass
    valores_fabrica = {
        "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
        "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
    }
    guardar_recetas_nube(valores_fabrica)
    return valores_fabrica

def guardar_recetas_nube(datos):
    try:
        requests.put(URL_RECETAS, data=json.dumps(datos), timeout=5)
    except Exception as e:
        st.error(f"Error al guardar recetas en la nube: {e}")

# --- SISTEMA DE RECARGA Y SINCRONIZACIÓN ---
# Botón flotante arriba para traer lo que haya editado tu pareja al instante
if st.button("🔄 Sincronizar / Traer cambios de mi pareja"):
    st.session_state.alacena_data = cargar_alacena_nube()
    st.session_state.recetas_data = cargar_recetas_nube()
    st.success("¡Datos actualizados con la nube!")
    st.rerun()

# Inicialización por primera vez en la sesión
if "alacena_data" not in st.session_state:
    st.session_state.alacena_data = cargar_alacena_nube()

if "recetas_data" not in st.session_state:
    st.session_state.recetas_data = cargar_recetas_nube()

# Formatear la tabla de la alacena
df_alacena = pd.DataFrame(list(st.session_state.alacena_data.items()), columns=["Ingrediente", "Cantidad"])

# Pestañas organizadas
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
                
                # Guardar el descuento de forma permanente en internet
                guardar_alacena_nube(st.session_state.alacena_data)
                st.balloons()
                st.success("¡Buen provecho! El stock se descontó de la nube para ambos.")
                st.rerun()
        else:
            st.error("No tienes suficientes ingredientes en la Alacena para este plato.")
    else:
        st.info("No hay platos guardados. Crea uno nuevo en la pestaña 'Recetas Compartidas'.")

# ==========================================
# 2. PESTAÑA: RECETAS
# ==========================================
with tab_recetas:
    st.header("📖 Recetario en la Nube")
    st.write("Platos que ambos pueden ver y elegir para cocinar:")
    
    for nombre_r, ing_r in sorted(st.session_state.recetas_data.items()):
        with st.expander(f"🍴 {nombre_r}"):
            st.write("**Ingredientes requeridos:**")
            for ing, cant in ing_r.items():
                st.write(f"- {ing}: {cant}")
            
            if st.button(f"🗑️ Eliminar {nombre_r}", key=f"del_{nombre_r}"):
                del st.session_state.recetas_data[nombre_r]
                guardar_recetas_nube(st.session_state.recetas_data)
                st.success(f"Receta '{nombre_r}' eliminada de la nube.")
                st.rerun()

    st.write("---")
    st.subheader("➕ Crear Nueva Receta")
    
    nombre_nueva_receta = st.text_input("Nombre del plato nuevo:").strip().title()
    ingredientes_disponibles = sorted(list(st.session_state.alacena_data.keys()))
    ings_elegidos = st.multiselect("Selecciona qué ingredientes de la alacena lleva:", ingredientes_disponibles)
    
    cantidades_ing = {}
    if ings_elegidos:
        st.write("✍️ **Escribe las cantidades necesarias:**")
        for ing in ings_elegidos:
            cantidades_ing[ing] = st.number_input(f"Cantidad de '{ing}':", min_value=1, value=100, key=f"cant_{ing}")
            
    if st.button("💾 Guardar Plato en el Recetario"):
        if not nombre_nueva_receta:
            st.error("Por favor, ponle un nombre al plato.")
        elif not cantidades_ing:
            st.error("Selecciona al menos un ingrediente.")
        else:
            st.session_state.recetas_data[nombre_nueva_receta] = cantidades_ing
            guardar_recetas_nube(st.session_state.recetas_data)
            st.success(f"¡Sincronizado! La receta '{nombre_nueva_receta}' ya es permanente.")
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
        btn_alacena = st.form_submit_button("Actualizar Alacena")
        
        if btn_alacena and nuevo_ing:
            if nuevo_ing in st.session_state.alacena_data:
                st.session_state.alacena_data[nuevo_ing] += nueva_cant
            else:
                st.session_state.alacena_data[nuevo_ing] = nueva_cant
            
            guardar_alacena_nube(st.session_state.alacena_data)
            st.success(f"¡Sincronizado! Se guardó permanente en la nube.")
            st.rerun()
