import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import time
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. CONFIGURAZIONE E BRANDING (AZ Golf Academy powered by Evot3ch)
# ==============================================================================
st.set_page_config(page_title="AZ Golf Academy | Powered by Evot3ch", page_icon="⛳", layout="wide")

COLORS = {
    'BrandOrange': '#FF9800', 
    'Dark': '#000000',         
    'White': '#FFFFFF',        
    'Grey': '#424242'
}

# CSS per pulizia interfaccia e branding
st.markdown(f"""
<style>
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stApp {{ background-color: {COLORS['White']}; }}
    .stButton>button {{ background-color: {COLORS['Dark']}; color: {COLORS['BrandOrange']}; border-radius: 8px; font-weight: bold; width: 100%; border: 2px solid {COLORS['Dark']}; }}
    .stButton>button:hover {{ background-color: {COLORS['BrandOrange']}; color: {COLORS['Dark']}; }}
    .metric-box {{ background: #FAFAFA; border-left: 5px solid {COLORS['BrandOrange']}; border-radius: 4px; padding: 15px; text-align: center; border: 1px solid #eee; }}
    .powered-by {{ font-size: 0.7rem; text-align: center; color: {COLORS['Grey']}; margin-top: 40px; letter-spacing: 3px; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SPLASH SCREEN (3 Secondi - Il tuo tocco professionale)
# ==============================================================================
if "splash_done" not in st.session_state:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("logo.png", use_container_width=True)
            except:
                st.markdown(f"<h1 style='text-align:center; font-size: 5rem; color:{COLORS['Dark']};'>AZ <span style='color:{COLORS['BrandOrange']};'>GOLF</span></h1><p style='text-align:center; color:{COLORS['Grey']}; letter-spacing:4px;'>ACADEMY SYSTEMS</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; margin-top:20px;'>Caricamento moduli Evot3ch...</p>", unsafe_allow_html=True)
    time.sleep(3.0)
    placeholder.empty()
    st.session_state["splash_done"] = True

# ==============================================================================
# 3. COSTANTI E DATA ENGINE (Identico al tuo originale per stabilità API)
# ==============================================================================
COLUMNS = ['User', 'Date', 'SessionName', 'Time', 'Category', 'Club', 'Start_Dist', 'Lie', 'Impact', 'Curvature', 'Height', 'Direction', 'Proximity', 'Rating']
CATEGORIES = ["LONG GAME / RANGE", "SHORT GAME", "PUTTING"]
CLUBS = ["DR", "3W", "5W", "7W", "3H", "3i", "4i", "5i", "6i", "7i", "8i", "9i", "PW", "AW", "GW", "SW", "LW"]

@st.cache_data(ttl=5)
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        df['Proximity'] = pd.to_numeric(df['Proximity'], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_shot(shot_data):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_existing = load_data()
    df_new = pd.DataFrame([shot_data])
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
    conn.update(data=df_final)
    st.cache_data.clear()

# ==============================================================================
# 4. LOGIN (Stile Academy)
# ==============================================================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f"<h3 style='color:{COLORS['BrandOrange']}; text-align:center;'>Accesso Piattaforma Pro</h3>", unsafe_allow_html=True)
        user_input = st.text_input("ID Atleta").upper().strip()
        pass_input = st.text_input("Master Password", type="password")
        if st.button("AUTENTICAZIONE"):
            if pass_input == "az.analytics" and user_input != "":
                st.session_state["logged_in"] = True
                st.session_state["user"] = user_input
                st.rerun()
            else:
                st.error("Credenziali respinte.")
        st.markdown(f"<p class='powered-by'>POWERED BY EVOT3CH</p>", unsafe_allow_html=True)
    st.stop()

# ==============================================================================
# 5. GENERATORE REPORT PDF (La tua logica originale dettagliata)
# ==============================================================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 8, 'AZ GOLF ACADEMY - PERFORMANCE REPORT', 0, 1, 'C')
        self.set_draw_color(255, 152, 0)
        self.line(10, 18, 200, 18)
        self.ln(6)

def generate_pro_pdf(df, user, period_name):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, f"ATLETA: {user} | PERIODO: {period_name} | DATA: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    for cat in CATEGORIES:
        df_cat = df[df['Category'] == cat]
        if df_cat.empty: continue
        pdf.set_font('Arial', 'B', 12)
        pdf.set_fill_color(0, 0, 0); pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, f" REPARTO: {cat} ", 0, 1, 'L', fill=True)
        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 6, f"Colpi: {len(df_cat)} | Voto Medio: {df_cat['Rating'].mean():.2f}/3.0", ln=True)
        pdf.ln(4)
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# ==============================================================================
# 6. INTERFACCIA PRINCIPALE (Mantenuta tua logica dei Tab e Form)
# ==============================================================================
st.sidebar.markdown(f"<h3 style='color:{COLORS['BrandOrange']}'>👤 {st.session_state['user']}</h3>", unsafe_allow_html=True)
session_name = st.sidebar.text_input("Sessione / Note", "Test Valutazione")

tab_in, tab_an = st.tabs(["🎯 TELEMETRIA", "📊 ANALYTICS"])

with tab_in:
    cat_scelta = st.radio("Area Tecnica", CATEGORIES, horizontal=True)
    with st.form("form_dati", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        start_dist = 0.0; lie = "-"; height = "-"; direction = "-"

        if cat_scelta == "LONG GAME / RANGE":
            with col1:
                club = st.selectbox("Bastone", CLUBS)
                impact = st.selectbox("Impatto", ["Solido", "Punta", "Tacco", "Shank", "Flappa", "Top"])
            with col2:
                curvature = st.selectbox("Curvatura", ["Dritta", "Push", "Pull", "Slice", "Hook"])
                height = st.selectbox("Altezza", ["Giusta", "Alta", "Bassa", "Rasoterra", "Flappa"])
            with col3:
                direction = st.selectbox("Direzione", ["Dritta", "Dx", "Sx"])
                proximity = st.number_input("Proximity Target (m)", min_value=0.0)
            voto = st.slider("Voto (1-3)", 1, 3, 2)
            
        elif cat_scelta == "SHORT GAME":
            with col1:
                club = st.selectbox("Bastone", ["LW", "SW", "GW", "AW", "PW", "9i", "8i"])
                start_dist = st.number_input("Distanza Partenza (m)", min_value=1.0)
            with col2:
                lie = st.selectbox("Lie", ["Fairway", "Rough", "Bunker", "Sponda"])
                impact = st.selectbox("Impatto", ["Solido", "Punta", "Tacco", "Shank", "Flappa", "Top"])
            with col3:
                curvature = st.selectbox("Curvatura Volo", ["Dritta", "Push", "Pull", "Slice", "Hook"])
                proximity = st.number_input("Proximity Finale (m)", min_value=0.0)
            voto = st.slider("Voto (1-3)", 1, 3, 2)
            
        else: # PUTTING
            club = "Putter"
            with col1: start_dist = st.number_input("Distanza Buco (m)", min_value=0.5)
            with col2: impact = st.selectbox("Faccia", ["Centro", "Punta", "Tacco"])
            with col3: curvature = st.selectbox("Linea", ["Dritta", "Push", "Pull"])
            proximity = st.number_input("Residua (m)", min_value=0.0)
            voto = st.slider("Voto (1-3)", 1, 3, 2)

        if st.form_submit_button("SALVA COLPO NEL DATABASE"):
            shot = {
                'User': st.session_state['user'], 'Date': datetime.date.today(),
                'SessionName': session_name, 'Time': datetime.datetime.now().strftime("%H:%M"),
                'Category': cat_scelta, 'Club': club, 'Start_Dist': start_dist, 'Lie': lie,
                'Impact': impact, 'Curvature': curvature, 'Height': height,
                'Direction': direction, 'Proximity': proximity, 'Rating': voto
            }
            save_shot(shot)
            st.toast("Dato acquisito da Evot3ch.", icon="✅")

with tab_an:
    df_all = load_data()
    df_u = df_all[df_all['User'] == st.session_state['user']]
    
    if df_u.empty:
        st.warning("Dati non disponibili.")
    else:
        # Dashboard Metriche (Tua logica originale)
        c1, c2, c3 = st.columns(3)
        c1.metric("Voto Medio", f"{df_u['Rating'].mean():.2f}")
        c2.metric("Colpi", len(df_u))
        c3.metric("Prox Media", f"{df_u['Proximity'].mean():.1f}m")
        
        # Grafico (Tua logica originale)
        fig = px.pie(df_u, names='Impact', title="Analisi Impatti", hole=0.3, color_discrete_sequence=['#FF9800', '#000000', '#424242'])
        st.plotly_chart(fig, use_container_width=True)

        # Download Report
        pdf_bytes = generate_pro_pdf(df_u, st.session_state['user'], "Lifelong Analysis")
        st.download_button("📄 SCARICA REPORT AZ (PDF)", data=pdf_bytes, file_name=f"AZ_Report_{st.session_state['user']}.pdf")

st.markdown(f"<p class='powered-by'>SYSTEMS ARCHITECTURE BY EVOT3CH</p>", unsafe_allow_html=True)

if st.sidebar.button("LOGOUT"):
    st.session_state.clear()
    st.rerun()

    
