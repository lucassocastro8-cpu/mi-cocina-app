import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la aplicación
st.set_page_config(page_title="Nuestra Cocina Conectada", page_icon="🍳", layout="centered")

st.title("🍳 Nuestra Cocina Sincronizada")
st.write("Conectado en tiempo real a Google Sheets para que ambos editen juntos.")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer los datos con diagnóstico de errores en pantalla
def cargar_alacena():
    try:
        # Corregido: ttl ahora es 0 (número) para evitar errores de conexión
        return conn.read(worksheet="Alacena", ttl=0) 
    except Exception as e:
        st.error("❌ Error al conectar con la planilla de Google.")
        # Esto nos va a decir en la pantalla el motivo exacto del fallo:
        st.info(f"🔍 Detalle técnico del error: {e}")
        return pd.DataFrame(columns=["Ingrediente", "Cantidad"])

# Cargar datos actuales
df_alacena = cargar_alacena()

# Asegurar que los tipos de datos sean correctos
if not df_alacena.empty:
    try:
        df_alacena["Cantidad"] = pd.to_numeric(df_alacena["Cantidad"])
    except Exception as e:
        st.warning("Nota: Hay un problema con el formato de los números en la planilla.")

# --- MENU DE PESTAÑAS ---
tab_cocina, tab_alacena = st.tabs(["🍳 Cocinar Hoy", "📦 Alacena Compartida"])

# ==========================================
# PESTAÑA: ALACENA (CONTROL DE STOCK)
# ==========================================
with tab_alacena:
    st.header("📦 Inventario en la Nube")
    
    if not df_alacena.empty:
        st.dataframe(df_alacena, use_container_width=True, hide_index=True)
    else:
        st.write("Aún no hay datos para mostrar.")

    st.write("---")
    st.subheader("➕ Agregar o Reponer Alimentos")
    
    with st.form("form_alacena"):
        nuevo_ing = st.text_input("Nombre del alimento (ej: Arroz, Leche):").strip().title()
        nueva_cant = st.number_input("Cantidad a sumar:", min_value=1, step=1)
        btn_alacena = st.form_submit_button("Actualizar en la Nube")
        
        if btn_alacena and nuevo_ing and not df_alacena.empty:
            if nuevo_ing in df_alacena["Ingrediente"].values:
                df_alacena.loc[df_alacena["Ingrediente"] == nuevo_ing, "Cantidad"] += nueva_cant
            else:
                nueva_fila = pd.DataFrame([{"Ingrediente": nuevo_ing, "Cantidad": nueva_cant}])
                df_alacena = pd.concat([df_alacena, nueva_fila], ignore_index=True)
            
            conn.update(worksheet="Alacena", data=df_alacena)
            st.success(f"¡Sincronizado! Se añadieron {nueva_cant} de '{nuevo_ing}'")
            st.rerun()

# ==========================================
# PESTAÑA: COCINA (DESCUENTO AUTOMÁTICO)
# ==========================================
with tab_cocina:
    st.header("🍳 ¿Qué preparamos para comer?")
    
    recetas = {
        "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
        "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
    }
    
    receta_elegida = st.selectbox("Elegir menú:", list(recetas.keys()))
    ingredientes_necesarios = recetas[receta_elegida]
    
    st.subheader("📋 Verificación de Stock")
    puede_cocinar = True
    
    stock_actual = dict(zip(df_alacena["Ingrediente"], df_alacena["Cantidad"])) if not df_alacena.empty else {}
    
    for ing, cant_req in ingredientes_necesarios.items():
        cant_disponible = stock_actual.get(ing, 0)
        
        if cant_disponible >= cant_req:
            st.write(f"✅ **{ing}**: Necesitas {cant_req} | Tienes {cant_disponible}")
        else:
            st.write(f"❌ **{ing}**: Necesitas {cant_req} | ¡Solo tienes {cant_disponible}! ⚠️")
            puede_cocinar = False
            
    st.write("---")
    
    if puede_cocinar and not df_alacena.empty:
        if st.button("🍽️ ¡Hecho! Cocinado", type="primary"):
            for ing, cant_req in ingredientes_necesarios.items():
                df_alacena.loc[df_alacena["Ingrediente"] == ing, "Cantidad"] -= cant_req
            
            conn.update(worksheet="Alacena", data=df_alacena)
            st.balloons()
            st.success("¡Buen provecho! El stock se descontó de la nube.")
            st.rerun()
    else:
        st.error("No se puede cocinar. Verifica los ingredientes o la conexión con la Alacena.")
