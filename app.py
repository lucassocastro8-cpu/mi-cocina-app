import streamlit as st
import pandas as pd
import requests

# Configuración visual de la aplicación
st.set_page_config(page_title="Nuestra Cocina Sincronizada", page_icon="🍳", layout="centered")

# --- BASE DE DATOS EN LA NUBE REAAL Y GRATUITA ---
# Usamos una URL única para vos y tu novia que saltea los bloqueos de Google
URL_DB = "https://keyvalue.xyz/v1/alacena-compartida-lucas-bren-2026"

st.title("🍳 Nuestra Cocina Sincronizada")
st.write("¡Inventario y recetas compartidas en tiempo real!")

# Funciones para leer y guardar en la nube sin usar contraseñas raras
def cargar_alacena_nube():
    try:
        respuesta = requests.get(URL_DB, timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json()
    except:
        pass
    # Stock inicial por defecto si la nube está vacía la primera vez
    return {
        "Arroz": 1000,
        "Fideos": 500,
        "Puré de Tomate": 2,
        "Cebolla": 4,
        "Carne Picada": 500
    }

def guardar_alacena_nube(datos):
    try:
        requests.put(URL_DB, json=datos, timeout=5)
    except Exception as e:
        st.error(f"Error de sincronización: {e}")

# Mantener los datos en la sesión actual
if "alacena_data" not in st.session_state:
    st.session_state.alacena_data = cargar_alacena_nube()

# Convertir datos a formato de tabla para mostrar
df_alacena = pd.DataFrame(list(st.session_state.alacena_data.items()), columns=["Ingrediente", "Cantidad"])

# Pestañas de la app
tab_cocina, tab_alacena = st.tabs(["🍳 Cocinar Hoy", "📦 Alacena Compartida"])

# ==========================================
# PESTAÑA: ALACENA
# ==========================================
with tab_alacena:
    st.header("📦 Inventario en la Nube")
    st.write("Lo que actualices acá se cambia en el teléfono de tu pareja al instante.")
    st.dataframe(df_alacena, use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("➕ Agregar o Reponer Alimentos")
    
    with st.form("form_alacena"):
        nuevo_ing = st.text_input("Nombre del alimento (ej: Leche, Aceite):").strip().title()
        nueva_cant = st.number_input("Cantidad a sumar:", min_value=1, step=1)
        btn_alacena = st.form_submit_button("Actualizar Alacena")
        
        if btn_alacena and nuevo_ing:
            if nuevo_ing in st.session_state.alacena_data:
                st.session_state.alacena_data[nuevo_ing] += nueva_cant
            else:
                st.session_state.alacena_data[nuevo_ing] = nueva_cant
            
            guardar_alacena_nube(st.session_state.alacena_data)
            st.success(f"¡Sincronizado! Se sumó {nuevo_ing}")
            st.rerun()

# ==========================================
# PESTAÑA: COCINA
# ==========================================
with tab_cocina:
    st.header("🍳 ¿Qué preparamos para comer?")
    
    # Recetario base fijo en el código
    recetas = {
        "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
        "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
    }
    
    receta_elegida = st.selectbox("Elegir menú:", list(recetas.keys()))
    ingredientes_necesarios = recetas[receta_elegida]
    
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
            st.success("¡Buen provecho! El stock se descontó de la nube correctamente.")
            st.rerun()
    else:
        st.error("No tienes suficientes ingredientes en casa para este plato.")
