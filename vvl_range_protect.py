import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import datetime
import os
import numpy as np

import streamlit as st

# 1. FUNZIONE PER IL CONTROLLO PASSWORD
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Accesso Riservato")
        password = st.text_input("Inserisci la password per il V.V.L. Commander", type="password")
        if st.button("Entra"):
            if password == "olimpiadi2040": # <-- SCEGLI LA TUA PASSWORD
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Password errata")
        return False
    return True

# 2. SE LA PASSWORD NON È CORRETTA, FERMA TUTTO
if not check_password():
    st.stop()

# --- DA QUI IN POI INCOLLA IL RESTO DEL TUO CODICE ---
st.title("🎯 V.V.L. COMMANDER")
# ... il resto del codice ...

# ==============================================================================
# 1. SETUP & STYLE
# ==============================================================================
st.set_page_config(page_title="V.V.L. Commander", page_icon="logo.png", layout="centered")

# Database File
DB_FILE = 'vvl_training_db.csv'

# Palette Colori Aggiornata
COLORS = {
    'Navy': '#1E3A8A',       # Header
    'Green': '#15803D',      # Putting / Success
    'Orange': '#C2410C',     # Short Game / Warn
    'Blue': '#2563EB',       # Range
    'Red': '#DC2626',        # Error / Shank
    'Grey': '#F3F4F6',
    'Gold': '#F59E0B'        # Stars
}

# Liste Bastoni e Distanze
CLUBS_FULL = ['Driver', 'Legno 3', 'Legno 5', 'Legno 7', 'Ibrido', 'Ferro 2', 'Ferro 3', 'Ferro 4', 
              'Ferro 5', 'Ferro 6', 'Ferro 7', 'Ferro 8', 'Ferro 9', 'PW', 'AW', 'GW', 'SW', 'LW']
CLUBS_WEDGE = ['LW', 'SW', 'GW', 'AW', 'PW', 'Ferro 9', 'Ferro 8']
DISTANCES_PUTT = ['1m', '2m', '3m', '4m', '5m', '6m', '8m', '10m', '12m', '15m', '20m', '>20m']

# Opzioni Proximity / Discostamento
PROXIMITY_RANGE = ["< 2m (Target)", "< 5m", "< 10m", "> 10m"]
PROXIMITY_SG = ["Given (<1m)", "Close (<3m)", "Ok (<5m)", "On Green (<10m)", "Miss (>10m)"]
DIR_ERROR = ["Dritta (Target)", "Sinistra (Pull/Hook)", "Destra (Push/Slice)"]

st.markdown(f"""
<style>
    .stApp {{ background-color: #FFFFFF; color: #111827; }}
    h1, h2, h3 {{ font-family: 'Helvetica', sans-serif; color: {COLORS['Navy']}; }}
    
    /* RADIO BUTTONS STYLE - Mobile Friendly */
    div[role="radiogroup"] > label > div:first-child {{ width: 22px !important; height: 22px !important; }}
    div[role="radiogroup"] label {{
        font-size: 15px !important; padding: 8px 12px;
        background-color: {COLORS['Grey']}; border-radius: 6px; margin: 3px;
        border: 1px solid #e5e7eb;
    }}
    div[role="radiogroup"] label:hover {{ border-color: {COLORS['Navy']}; background-color: #dbeafe; }}
    
    /* SUBMIT BUTTON */
    .stButton>button {{
        color: white; font-size: 20px !important; padding: 12px 0;
        border-radius: 8px; font-weight: bold; width: 100%; border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.1s;
    }}
    .stButton>button:active {{ transform: scale(0.98); }}
    
    /* METRIC CARDS */
    .metric-box {{
        background: white; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .metric-num {{ font-size: 1.8rem; font-weight: 800; color: {COLORS['Navy']}; }}
    .metric-lbl {{ font-size: 0.8rem; text-transform: uppercase; color: #6b7280; letter-spacing: 0.5px; }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATA ENGINE
# ==============================================================================

def init_db():
    # Parametri mappati dinamicamente:
    # Mode | Param1 | Param2 | Param3 | Param4 | Param5 | Param6
    # Range| Club   | Impact | Shape  | DistCnt| Prox   | DirErr
    # SG   | Club   | Impact | Lie    | DistCnt| Prox   | -
    # Putt | Dist   | Impact | Line   | Speed  | -      | -
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=['Date', 'SessionName', 'Time', 'Mode', 
                                   'Param1', 'Param2', 'Param3', 'Param4', 'Param5', 'Param6', 'Voto'])
        df.to_csv(DB_FILE, index=False)

def load_data():
    init_db()
    try:
        df = pd.read_csv(DB_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except:
        return pd.DataFrame()

def save_shot(date, session_name, mode, p1, p2, p3, p4, p5, p6, rating):
    new_data = {
        "Date": date, "SessionName": session_name, "Time": datetime.datetime.now().strftime("%H:%M:%S"),
        "Mode": mode, "Param1": p1, "Param2": p2, "Param3": p3, "Param4": p4, "Param5": p5, "Param6": p6,
        "Voto": rating
    }
    df_new = pd.DataFrame([new_data])
    header = not os.path.exists(DB_FILE)
    df_new.to_csv(DB_FILE, mode='a', header=header, index=False)

# ==============================================================================
# 3. PDF REPORT ENGINE
# ==============================================================================
class CommanderPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, 'V.V.L. RANGE COMMANDER- REPORT', 0, 1, 'C')
        self.line(10, 20, 200, 20)
        self.ln(5)

def generate_pdf(df, title_period, mode):
    pdf = CommanderPDF()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"MODALITA': {mode} | {title_period}", ln=True)
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 6, f"Generato il: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)
    
    # Mapping Colonne
    cols = []
    if mode == 'RANGE':
        cols = [('Bastone', 'Param1', 25), ('Impatto', 'Param2', 25), ('Target', 'Param5', 30), ('Errore', 'Param6', 30), ('Voto', 'Voto', 15)]
    elif mode == 'SHORT GAME':
        cols = [('Bastone', 'Param1', 20), ('Impatto', 'Param2', 25), ('Lie', 'Param3', 25), ('Prox.', 'Param5', 35), ('Voto', 'Voto', 15)]
    else: # PUTTING
        cols = [('Dist.', 'Param1', 25), ('Impatto', 'Param2', 25), ('Linea', 'Param3', 25), ('Esito', 'Param4', 30), ('Voto', 'Voto', 15)]

    # Stats Summary
    avg_vote = df['Voto'].mean()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"Colpi Totali: {len(df)} | Voto Medio: {avg_vote:.2f}/3.0", ln=True, fill=False)
    
    # Errore Shank
    shanks = len(df[df['Param2'] == 'Shank'])
    if shanks > 0:
        pdf.set_text_color(220, 38, 38)
        pdf.cell(0, 6, f"ATTENZIONE: {shanks} Shank registrati!", ln=True)
        pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Tabella
    pdf.set_font('Arial', 'B', 8)
    for name, _, w in cols:
        pdf.cell(w, 7, name, 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font('Courier', '', 8)
    # Stampa max 500 righe per non esplodere
    for _, row in df.head(500).iterrows():
        for _, db_col, w in cols:
            val = str(row[db_col])
            # Accorcia stringhe lunghe
            if len(val) > 15: val = val[:13] + ".."
            pdf.cell(w, 6, val, 1, 0, 'C')
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 4. MAIN APP LOGIC
# ==============================================================================

st.title("🎯 V.V.L. COMMANDER PRO")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    mode = st.radio("MODALITÀ:", ["RANGE", "SHORT GAME", "PUTTING"], index=0)
    st.divider()
    session_date = st.date_input("Data", datetime.date.today())
    session_name = st.text_input("Nome Sessione", value=f"Allenamento {mode}")
    
    # Colore Bottone in base alla modalità
    if mode == "RANGE": btn_c = COLORS['Blue']
    elif mode == "PUTTING": btn_c = COLORS['Green']
    else: btn_c = COLORS['Orange']
    
    st.markdown(f"""<style>.stButton>button {{ background-color: {btn_c} !important; }}</style>""", unsafe_allow_html=True)

# --- TABS ---
tab_input, tab_analysi = st.tabs([f"🏌️ INPUT {mode}", "📈 ANALISI & GRAFICI"])

# ==========================
# TAB 1: INPUT AVANZATO
# ==========================
with tab_input:
    with st.form("shot_entry", clear_on_submit=False):
        
        # --- RANGE MODE ---
        if mode == "RANGE":
            st.markdown("### 🏹 LONG GAME & IRONS")
            c_top1, c_top2 = st.columns(2)
            with c_top1: p1 = st.selectbox("Bastone:", CLUBS_FULL, index=10)
            
            # Riga 1: Contatto e Volo
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**💥 Impatto**")
                p2 = st.radio("Imp", ["Solido", "Top", "Flappa", "Tacco", "Punta", "Shank"], label_visibility="collapsed")
            with c2:
                st.markdown("**🚀 Volo Palla**")
                p3 = st.radio("Volo", ["Dritta", "Draw", "Fade", "Push", "Pull", "Hook", "Slice"], label_visibility="collapsed")
            
            st.markdown("---")
            st.markdown("### 🎯 DISPERSIONE E TARGET")
            
            # Riga 2: Distanza Controllo e Direzione Errore
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("**📏 Lunghezza**")
                p4 = st.radio("Len", ["Giusta", "Corta", "Lunga"], horizontal=True, label_visibility="collapsed")
            with c4:
                st.markdown("**🧭 Direzione Errore**")
                p6 = st.radio("Dir", DIR_ERROR, label_visibility="collapsed")
            
            # Riga 3: Quantificazione Errore
            st.markdown("**📐 Discostamento dal Target (Proximity)**")
            p5 = st.select_slider("Quanto lontano?", options=PROXIMITY_RANGE, value="< 10m")
            
            st.markdown("**⭐ Voto (Qualità Colpo)**")
            rating = st.slider("Rating", 1, 3, 2, format="⭐ %d")

        # --- SHORT GAME MODE ---
        elif mode == "SHORT GAME":
            st.markdown("### 🏖️ PITCH, CHIP & BUNKER")
            c_top1, c_top2 = st.columns(2)
            with c_top1: p1 = st.selectbox("Bastone:", CLUBS_WEDGE, index=1)
            with c_top2: p3 = st.selectbox("Lie:", ["Fairway", "Rough", "Bunker", "Sponda"])
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**💥 Impatto**")
                p2 = st.radio("Imp", ["Solido", "Flappa", "Top", "Doppio Tocco", "Shank"], label_visibility="collapsed")
            with c2:
                st.markdown("**📏 Controllo**")
                p4 = st.radio("Ctrl", ["Giusta", "Corta", "Lunga"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("---")
            st.markdown("**🎯 Proximity (Distanza dalla buca)**")
            p5 = st.select_slider("Proximity", options=PROXIMITY_SG, value="Ok (<5m)")
            p6 = "-" # Non usato
            
            st.markdown("**⭐ Voto**")
            rating = st.radio("Voto", [1, 2, 3], horizontal=True, format_func=lambda x: f"{x} ⭐")

        # --- PUTTING MODE ---
        elif mode == "PUTTING":
            st.markdown("### ⛳ PUTTING LAB")
            p1 = st.select_slider("Distanza Buca:", options=DISTANCES_PUTT, value='3m')
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**🔨 Impatto**")
                p2 = st.radio("Imp", ["Centro", "Punta", "Tacco"], horizontal=True, label_visibility="collapsed")
                st.markdown("**🏎️ Velocità**")
                p4 = st.radio("Speed", ["Giusta", "Corta", "Lunga"], horizontal=True, label_visibility="collapsed")
            with c2:
                st.markdown("**📐 Linea**")
                p3 = st.radio("Linea", ["Dritta", "Push (Dx)", "Pull (Sx)"], label_visibility="collapsed")
            
            st.markdown("---")
            st.markdown("**⭐ Voto Adattato** (Considera la distanza!)")
            rating = st.radio("Rate", [1, 2, 3], horizontal=True, 
                              format_func=lambda x: "3 (Imbucata/Perfetto)" if x==3 else ("2 (Data/Bordo)" if x==2 else "1 (Errore)"))
            p5, p6 = "-", "-" # Non usati

        # SUBMIT
        st.markdown("---")
        if st.form_submit_button(f"REGISTRA COLPO {mode} ✅"):
            save_shot(session_date, session_name, mode, p1, p2, p3, p4, p5, p6, rating)
            st.toast("Dati Salvati!", icon="💾")

# ==========================
# TAB 2: ANALISI PRO
# ==========================
with tab_analysi:
    df_full = load_data()
    
    if not df_full.empty:
        df_mode = df_full[df_full['Mode'] == mode]
        
        if not df_mode.empty:
            # Filtri Temporali
            periods = ["Sessione Corrente", "Ultimi 7 Giorni", "Mese Corrente", "Stagione (9 Mesi)", "Lifelong"]
            sel_period = st.selectbox("📅 Periodo Analisi:", periods)
            
            # Logica Filtro Data
            today = datetime.date.today()
            if "Sessione" in sel_period:
                df_view = df_mode[(df_mode['Date'] == session_date) & (df_mode['SessionName'] == session_name)]
            elif "Lifelong" in sel_period:
                df_view = df_mode
            else:
                days = 7 if "7" in sel_period else (30 if "Mese" in sel_period else 270)
                df_view = df_mode[df_mode['Date'] >= (today - datetime.timedelta(days=days))]

            if not df_view.empty:
                # --- KPI SECTION ---
                col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                
                # Calcoli Specifici
                total_shots = len(df_view)
                avg_r = df_view['Voto'].mean()
                shank_cnt = len(df_view[df_view['Param2'] == 'Shank'])
                
                # Consistency Score (Deviazione Standard inversa)
                consistency = (1 - df_view['Voto'].std()/3) * 100 if total_shots > 1 else 0
                
                col_k1.markdown(f'<div class="metric-box"><div class="metric-num">{total_shots}</div><div class="metric-lbl">Colpi</div></div>', unsafe_allow_html=True)
                col_k2.markdown(f'<div class="metric-box"><div class="metric-num">{avg_r:.2f}</div><div class="metric-lbl">Voto Medio</div></div>', unsafe_allow_html=True)
                col_k3.markdown(f'<div class="metric-box"><div class="metric-num" style="color:{COLORS["Green"]}">{consistency:.0f}%</div><div class="metric-lbl">Consistenza</div></div>', unsafe_allow_html=True)
                col_k4.markdown(f'<div class="metric-box"><div class="metric-num" style="color:{COLORS["Red"]}">{shank_cnt}</div><div class="metric-lbl">Shanks</div></div>', unsafe_allow_html=True)

                st.divider()

                # --- GRAFICI AVANZATI ---
                
                # 1. DISPERSION PLOT (Solo Range/SG)
                if mode in ["RANGE", "SHORT GAME"]:
                    st.markdown("### 🎯 Analisi Dispersione (Simulazione)")
                    
                    # Creiamo coordinate fittizie per visualizzare la dispersione
                    # Mappiamo Param6 (Dir) su X e Param4 (Len) su Y
                    def map_x(row):
                        base = 0
                        if "Sinistra" in str(row['Param6']): base = -1
                        elif "Destra" in str(row['Param6']): base = 1
                        return base + np.random.normal(0, 0.15) # Jitter

                    def map_y(row):
                        base = 0
                        if str(row['Param4']) == "Corta": base = -1
                        elif str(row['Param4']) == "Lunga": base = 1
                        return base + np.random.normal(0, 0.15)
                    
                    if mode == "RANGE":
                        df_view['Disp_X'] = df_view.apply(map_x, axis=1)
                        df_view['Disp_Y'] = df_view.apply(map_y, axis=1)
                        
                        

                        fig_disp = px.scatter(df_view, x='Disp_X', y='Disp_Y', color='Param5',
                                            title="Dispersione Colpi (Centro = Target)",
                                            labels={'Disp_X': 'Direzione', 'Disp_Y': 'Controllo Distanza'},
                                            category_orders={"Param5": PROXIMITY_RANGE},
                                            color_discrete_sequence=px.colors.qualitative.G10)
                        
                        # Add target lines
                        fig_disp.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                        fig_disp.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
                        fig_disp.update_xaxes(showticklabels=False, range=[-2, 2])
                        fig_disp.update_yaxes(showticklabels=False, range=[-2, 2])
                        st.plotly_chart(fig_disp, use_container_width=True)
                
                # 2. CONSISTENCY OVER TIME
                st.markdown("### 📈 Consistenza nel Tempo")
                # Media mobile su finestra di 5 colpi
                df_view['Moving_Avg'] = df_view['Voto'].rolling(window=5, min_periods=1).mean()
                fig_trend = px.line(df_view, y='Moving_Avg', title="Andamento Voto (Media Mobile)", markers=True)
                fig_trend.update_traces(line_color=COLORS['Navy'])
                fig_trend.update_layout(yaxis_range=[0.5, 3.5])
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # 3. DISTRIBUZIONI
                c_g1, c_g2 = st.columns(2)
                with c_g1:
                    st.markdown("#### Tipo di Errore (Impatto)")
                    fig_pie = px.pie(df_view, names='Param2', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with c_g2:
                    dist_col = 'Param5' if mode != "PUTTING" else 'Param1'
                    st.markdown(f"#### Voto Medio Colpo")
                    fig_bar = px.histogram(df_view, x=dist_col, color='Voto', barmode='group')
                    st.plotly_chart(fig_bar, use_container_width=True)

                # REPORT PDF
                st.divider()
                pdf_data = generate_pdf(df_view, sel_period, mode)
                st.download_button(
                    label="📥 SCARICA REPORT COMPLETO (PDF)",
                    data=pdf_data,
                    file_name=f"VVL_ProReport_{mode}_{datetime.date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.info("Nessun dato per il periodo selezionato.")
        else:

            st.warning(f"Nessuna sessione di {mode} registrata.")
