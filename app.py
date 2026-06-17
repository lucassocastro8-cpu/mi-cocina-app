import streamlit as st
import pandas as pd
import requests

# Configuración visual de la aplicación
st.set_page_config(page_title="Nuestra Cocina Sincronizada", page_icon="🍳", layout="centered")

# --- BASES DE DATOS EN LA NUBE REAAL Y GRATUITA ---
URL_ALACENA = "https://keyvalue.xyz/v1/alacena-compartida-lucas-bren-2026"
URL_RECETAS = "https://keyvalue.xyz/v1/recetas-compartidas-lucas-bren-2026"

st.title("🍳 Nuestra Cocina Sincronizada")
st.write("¡Inventario y recetario compartidos en tiempo real por la nube!")

# --- FUNCIONES: ALACENA ---
def cargar_alacena_nube():
    try:
        respuesta = requests.get(URL_ALACENA, timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json()
    except:
        pass
    return {"Arroz": 1000, "Fideos": 500, "Puré de Tomate": 2, "Cebolla": 4, "Carne Picada": 500}

def guardar_alacena_nube(datos):
    try: requests.put(URL_ALACENA, json=datos, timeout=5)
    except Exception as e: st.error(f"Error de sincronización de alacena: {e}")

# --- FUNCIONES: RECETAS ---
def cargar_recetas_nube():
    try:
        respuesta = requests.get(URL_RECETAS, timeout=5)
        if respuesta.status_code == 200:
            return respuesta.json()
    except:
        pass
    # Recetas por defecto iniciales
    return {
        "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
        "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
    }

def guardar_recetas_nube(datos):
    try: requests.put(URL_RECETAS, json=datos, timeout=5)
    except Exception as e: st.error(f"Error de sincronización de recetas: {e}")

# Mantener los datos vivos en la sesión actual
if "alacena_data" not in st.session_state:
    st.session_state.alacena_data = cargar_alacena_nube()

if "recetas_data" not in st.session_state:
    st.session_state.recetas_data = cargar_recetas_nube()

# Formatear alacena para mostrar
df_alacena = pd.DataFrame(list(st.session_state.alacena_data.items()), columns=["Ingrediente", "Cantidad"])

# LAS TRES PESTAÑAS (Añadida la de Recetas en el medio)
tab_cocina, tab_recetas, tab_alacena = st.tabs(["🍳 Cocinar Hoy", "📖 Recetas Compartidas", "📦 Alacena Compartida"])

# ==========================================
# 1. PESTAÑA: COCINA (Ajustada para leer tus recetas dinámicas)
# ==========================================
with tab_cocina:
    st.header("🍳 ¿Qué preparamos para comer?")
    
    opciones_recetas = list(st.session_state.recetas_data.keys())
    
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
                st.success("¡Buen provecho! El stock se descontó de la nube correctamente.")
                st.rerun()
        else:
            st.error("No tienes suficientes ingredientes en la Alacena para este plato.")
    else:
        st.info("No hay platos guardados. Crea uno nuevo en la pestaña 'Recetas Compartidas'.")

# ==========================================
# 2. PESTAÑA: RECETAS (¡NUEVA SOLAPA SOLICITADA!)
# ==========================================
with tab_recetas:
    st.header("📖 Recetario en la Nube")
    st.write("Estos son los platos guardados que ambos pueden elegir:")
    
    # Mostrar recetas que ya existen
    for nombre_r, ing_r in st.session_state.recetas_data.items():
        with st.expander(f"🍴 {nombre_r}"):
            st.write("**Ingredientes e insumos requeridos:**")
            for ing, cant in ing_r.items():
                st.write(f"- {ing}: {cant}")
            
            # Botón opcional por si quieren borrar alguna receta vieja
            if st.button(f"🗑️ Eliminar {nombre_r}", key=f"del_{nombre_r}"):
                del st.session_state.recetas_data[nombre_r]
                guardar_recetas_nube(st.session_state.recetas_data)
                st.success(f"Receta '{nombre_r}' eliminada.")
                st.rerun()

    st.write("---")
    st.subheader("➕ Crear Nueva Receta")
    
    # Formulario dinámico e interactivo
    nombre_nueva_receta = st.text_input("Nombre del plato (ej: Milanesas con Puré):").strip().title()
    
    # Toma los nombres de comida que tienes creados en la Alacena
    ingredientes_disponibles = sorted(list(st.session_state.alacena_data.keys()))
    ings_elegidos = st.multiselect("Selecciona qué ingredientes lleva este plato:", ingredientes_disponibles)
    
    cantidades_ing = {}
    if ings_elegidos:
        st.write("✍️ **Escribe cuánto consume el plato de cada ingrediente:**")
        for ing in ings_elegidos:
            cantidades_ing[ing] = st.number_input(f"Cantidad necesaria de '{ing}':", min_value=1, value=100, key=f"cant_{ing}")
            
    if st.button("💾 Guardar Plato en el Recetario"):
        if not nombre_nueva_receta:
            st.error("Por favor, ponle un nombre al plato para guardarlo.")
        elif not cantidades_ing:
            st.error("Debes seleccionar al menos un ingrediente para la receta.")
        else:
            # Guardar en local y subir a la nube
            st.session_state.recetas_data[nombre_nueva_receta] = cantidades_ing
            guardar_recetas_nube(st.session_state.recetas_data)
            st.success(f"¡Sincronizado! La receta '{nombre_nueva_receta}' ya está disponible.")
            st.rerun()

# ==========================================
# 3. PESTAÑA: ALACENA
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
