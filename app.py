import streamlit as st
import pandas as pd
import requests

# Configuración visual de la aplicación
st.set_page_config(page_title="Nuestra Cocina Sincronizada", page_icon="🍳", layout="centered")

# --- CONEXIÓN DIRECTA A TU BASE DE DATOS REAL (FIREBASE) ---
# Buscamos la URL de forma segura en los Secrets de Streamlit
URL_BASE_FIREBASE = st.secrets.get("FIREBASE_URL", "https://CAMBIA_ESTO_POR_TU_URL.firebaseio.com/")

# Nos aseguramos de que la URL termine en barra diagonal
if not URL_BASE_FIREBASE.endswith("/"):
    URL_BASE_FIREBASE += "/"

URL_ALACENA = f"{URL_BASE_FIREBASE}alacena.json"
URL_RECETAS = f"{URL_BASE_FIREBASE}recetas.json"

# --- FUNCIONES DE LECTURA Y ESCRITURA EN TIEMPO REAL ---
def cargar_alacena():
    try:
        res = requests.get(URL_ALACENA, timeout=5)
        if res.status_code == 200 and res.json() is not None:
            return res.json()
    except:
        pass
    # Si la base de datos está vacía (primera vez absoluta), la inicializamos
    inicial = {"Arroz": 1000, "Fideos": 500, "Puré de Tomate": 2, "Cebolla": 4, "Carne Picada": 500}
    requests.put(URL_ALACENA, json=inicial, timeout=5)
    return inicial

def guardar_alacena(datos):
    try:
        requests.put(URL_ALACENA, json=datos, timeout=5)
    except Exception as e:
        st.error(f"Error de red al guardar alacena: {e}")

def cargar_recetas():
    try:
        res = requests.get(URL_RECETAS, timeout=5)
        if res.status_code == 200 and res.json() is not None:
            return res.json()
    except:
        pass
    # Recetas iniciales de fábrica
    inicial = {
        "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
        "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
    }
    requests.put(URL_RECETAS, json=inicial, timeout=5)
    return inicial

def guardar_recetas(datos):
    try:
        requests.put(URL_RECETAS, json=datos, timeout=5)
    except Exception as e:
        st.error(f"Error de red al guardar recetas: {e}")

# --- TRAER DATOS FRESCOS DE GOOGLE EN CADA CLIC ---
alacena_data = cargar_alacena()
recetas_data = cargar_recetas()

# Formatear la tabla para la pestaña de inventario
df_alacena = pd.DataFrame(list(alacena_data.items()), columns=["Ingrediente", "Cantidad"])

st.title("🍳 Nuestra Cocina Sincronizada")
st.write("Conectado a una base de datos real. ¡Inmortal y compartida en la nube!")

# Pestañas de la aplicación
tab_cocina, tab_recetas, tab_alacena = st.tabs(["🍳 Cocinar Hoy", "📖 Recetas Compartidas", "📦 Alacena Compartida"])

# ==========================================
# 1. PESTAÑA: COCINA
# ==========================================
with tab_cocina:
    st.header("🍳 ¿Qué preparamos para comer?")
    opciones = sorted(list(recetas_data.keys()))
    
    if opciones:
        receta_elegida = st.selectbox("Elegir menú:", opciones)
        ingredientes_necesarios = recetas_data[receta_elegida]
        
        st.subheader("📋 Verificación de Stock")
        puede_cocinar = True
        
        for ing, cant_req in ingredientes_necesarios.items():
            cant_disponible = alacena_data.get(ing, 0)
            if cant_disponible >= cant_req:
                st.write(f"✅ **{ing}**: Necesitas {cant_req} | Tienes {cant_disponible}")
            else:
                st.write(f"❌ **{ing}**: Necesitas {cant_req} | ¡Solo tienes {cant_disponible}! ⚠️")
                puede_cocinar = False
                
        st.write("---")
        if puede_cocinar:
            if st.button("🍽️ ¡Hecho! Cocinado", type="primary"):
                for ing, cant_req in ingredientes_necesarios.items():
                    alacena_data[ing] -= cant_req
                guardar_alacena(alacena_data)
                st.balloons()
                st.success("¡Buen provecho! El stock se descontó de la base de datos.")
                st.rerun()
        else:
            st.error("Faltan ingredientes en la Alacena para este plato.")
    else:
        st.info("Crea un plato en la pestaña 'Recetas Compartidas' para empezar.")

# ==========================================
# 2. PESTAÑA: RECETAS
# ==========================================
with tab_recetas:
    st.header("📖 Recetario en la Base de Datos")
    
    for nombre_r, ing_r in sorted(recetas_data.items()):
        with st.expander(f"🍴 {nombre_r}"):
            st.write("**Ingredientes necesarios:**")
            for ing, cant in ing_r.items():
                st.write(f"- {ing}: {cant}")
            if st.button(f"🗑️ Eliminar {nombre_r}", key=f"del_{nombre_r}"):
                del recetas_data[nombre_r]
                guardar_recetas(recetas_data)
                st.rerun()

    st.write("---")
    st.subheader("➕ Crear Nueva Receta")
    nombre_nueva_receta = st.text_input("Nombre del plato nuevo:").strip().title()
    ingredientes_disponibles = sorted(list(alacena_data.keys()))
    ings_elegidos = st.multiselect("Selecciona qué ingredientes lleva:", ingredientes_disponibles)
    
    cantidades_ing = {}
    if ings_elegidos:
        for ing in ings_elegidos:
            cantidades_ing[ing] = st.number_input(f"Cantidad de '{ing}':", min_value=1, value=100, key=f"cant_{ing}")
            
    if st.button("💾 Guardar Plato en el Recetario"):
        if nombre_nueva_receta and cantidades_ing:
            recetas_data[nombre_nueva_receta] = cantidades_ing
            guardar_recetas(recetas_data)
            st.success("¡Receta guardada de forma permanente!")
            st.rerun()

# ==========================================
# 3. PESTAÑA: ALACENA
# ==========================================
with tab_alacena:
    st.header("📦 Inventario Permanente")
    st.dataframe(df_alacena, use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("➕ Agregar o Reponer Alimentos")
    with st.form("form_alacena"):
        nuevo_ing = st.text_input("Nombre del alimento:").strip().title()
        nueva_cant = st.number_input("Cantidad a sumar:", min_value=1, step=1)
        if st.form_submit_button("Actualizar Alacena") and nuevo_ing:
            if nuevo_ing in alacena_data:
                alacena_data[nuevo_ing] += nueva_cant
            else:
                alacena_data[nuevo_ing] = nueva_cant
            guardar_alacena(alacena_data)
            st.rerun()
