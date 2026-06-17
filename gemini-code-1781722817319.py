import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración de la aplicación
st.set_page_config(page_title="Nuestra Cocina Conectada", page_icon="🍳", layout="centered")

st.title("🍳 Nuestra Cocina Sincronizada")
st.write("Conectado en tiempo real a Google Sheets para que ambos editen juntos.")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Creamos la conexión usando las herramientas nativas de Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer los datos actualizados de la Alacena
def cargar_alacena():
    try:
        # Lee la pestaña "Alacena" de tu planilla
        return conn.read(worksheet="Alacena", ttl="0") # ttl="0" evita que guarde caché vieja
    except Exception as e:
        st.error("Error al conectar con la planilla de Google. Revisa las credenciales.")
        return pd.DataFrame(columns=["Ingrediente", "Cantidad"])

# Función para guardar datos en la Alacena de Google Drive
def guardar_alacena(df):
    conn.update(worksheet="Alacena", data=df)

# Cargar datos actuales
df_alacena = cargar_alacena()

# Asegurar que los tipos de datos sean correctos
if not df_alacena.empty:
    df_alacena["Cantidad"] = pd.to_numeric(df_alacena["Cantidad"])

# --- MENU DE PESTAÑAS ---
tab_cocina, tab_alacena = st.tabs(["🍳 Cocinar Hoy", "📦 Alacena Compartida"])

# ==========================================
# PESTAÑA: ALACENA (CONTROL DE STOCK)
# ==========================================
with tab_alacena:
    st.header("📦 Inventario en la Nube")
    st.write("Lo que cargues acá lo verá tu pareja al instante.")
    
    # Mostrar tabla actual
    if not df_alacena.empty:
        st.dataframe(df_alacena, use_container_width=True, hide_index=True)
    else:
        st.info("La alacena está vacía en Google Sheets.")

    st.write("---")
    st.subheader("➕ Agregar o Reponer Alimentos")
    
    with st.form("form_alacena"):
        nuevo_ing = st.text_input("Nombre del alimento (ej: Arroz, Leche):").strip().title()
        nueva_cant = st.number_input("Cantidad a sumar:", min_value=1, step=1)
        btn_alacena = st.form_submit_button("Actualizar en la Nube")
        
        if btn_alacena and nuevo_ing:
            # Si ya existe, sumamos el stock. Si no, lo agregamos como fila nueva.
            if nuevo_ing in df_alacena["Ingrediente"].values:
                df_alacena.loc[df_alacena["Ingrediente"] == nuevo_ing, "Cantidad"] += nueva_cant
            else:
                nueva_fila = pd.DataFrame([{"Ingrediente": nuevo_ing, "Cantidad": nueva_cant}])
                df_alacena = pd.concat([df_alacena, nueva_fila], ignore_index=True)
            
            # Subir cambios a Google Sheets
            guardar_alacena(df_alacena)
            st.success(f"¡Sincronizado! Se añadieron {nueva_cant} de '{nuevo_ing}'")
            st.rerun()

# ==========================================
# PESTAÑA: COCINA (DESCUENTO AUTOMÁTICO)
# ==========================================
with tab_cocina:
    st.header("🍳 ¿Qué preparamos para comer?")
    
    # Definimos las recetas base directamente en el código para simplificar,
    # pero los ingredientes los busca y descuenta del Google Sheets real.
    recetas = {
        "Fideos con Tuco": {"Fideos": 250, "Puré de Tomate": 1, "Cebolla": 1},
        "Arroz con Carne": {"Arroz": 200, "Carne Picada": 300, "Cebolla": 1}
    }
    
    receta_elegida = st.selectbox("Elegir menú:", list(recetas.keys()))
    ingredientes_necesarios = recetas[receta_elegida]
    
    st.subheader("📋 Verificación de Stock")
    puede_cocinar = True
    
    # Diccionario auxiliar para chequear stock fácil
    stock_actual = dict(zip(df_alacena["Ingrediente"], df_alacena["Cantidad"])) if not df_alacena.empty else {}
    
    for ing, cant_req in ingredientes_necesarios.items():
        cant_disponible = stock_actual.get(ing, 0)
        
        if cant_disponible >= cant_req:
            st.write(f"✅ **{ing}**: Necesitas {cant_req} | Tienes {cant_disponible}")
        else:
            st.write(f"❌ **{ing}**: Necesitas {cant_req} | ¡Solo tienes {cant_disponible}! ⚠️")
            puede_cocinar = False
            
    st.write("---")
    
    if puede_cocinar:
        if st.button("🍽️ ¡Hecho! Cocinado", type="primary"):
            # Restar los ingredientes del DataFrame de Pandas
            for ing, cant_req in ingredientes_necesarios.items():
                df_alacena.loc[df_alacena["Ingrediente"] == ing, "Cantidad"] -= cant_req
            
            # Guardar el nuevo inventario reducido en Google Sheets
            guardar_alacena(df_alacena)
            st.balloons()
            st.success("¡Buen provecho! El stock se descontó de la nube. Tu novia ya lo puede ver actualizado.")
            st.rerun()
    else:
        st.error("Faltan ingredientes en la Alacena para poder realizar este plato.")