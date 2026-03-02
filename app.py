import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import locale

# --- 1. FUNZIONE LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        st.markdown("<style>.stApp { background-color: #000000; }</style>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if os.path.exists("logo.png"): st.image("logo.png", width=200)
            st.subheader("Area Riservata Maldarizzi")
            user = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Accedi"):
                if user == "Preventivatore26" and password == "cipiacemigliorare":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Credenziali errate")
        return False
    return True

if check_password():
    # --- 2. CLASSE PDF "MALDARIZZI WHITE EDITION" ---
    class MaldarizziPDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_margins(10, 10, 10)
            self.set_auto_page_break(False)
            if os.path.exists("Rubik-Light.ttf"):
                self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
            if os.path.exists("Rubik-Bold.ttf"):
                self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
            self.f_f = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

        def header(self):
            # BARRA SUPERIORE NERA
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 40, 'F')
            
            # Logo al centro sulla barra nera
            if os.path.exists("logo.png"):
                self.image("logo.png", 75, 8, 60)
            
            # Scritta centrata sotto la barra nera (testo nero su fondo bianco)
            self.set_y(45)
            self.set_font(self.f_f, "B", 22)
            self.set_text_color(0, 0, 0)
            self.cell(0, 10, "IL TUO PREVENTIVO", align="C", ln=True)

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
    
    # Gestione Data Italiana
    try:
        locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
    except:
        pass # Fallback se il sistema non ha il locale italiano

    # Sidebar
    st.sidebar.header("📁 Database")
    uploaded_excel = st.sidebar.file_uploader("Carica Listino", type=["xlsx"])
    if uploaded_excel:
        with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
        st.sidebar.success("Database aggiornato!")

    if not os.path.exists("dati.xlsx"):
        st.error("Carica dati.xlsx")
        st.stop()

    excel = pd.ExcelFile("dati.xlsx")
    foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
    df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
    
    st.sidebar.markdown("---")
    g_validita = st.sidebar.slider("Validità", 1, 30, 30)
    nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
    email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
    tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

    c1, c2 = st.columns(2)
    with c1:
        nome_cliente = st.text_input("Cliente", "Gentile CLIENTE")
        t_veicolo = st.radio("Stato", ["Nuovo", "Usato"], horizontal=True)
    with c2:
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique().tolist()))
        # Modello serve per il filtro, ma non lo stamperemo
        modello = st.selectbox("Modello (Filtro)", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique().tolist()))
        versione = st.selectbox("Versione", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique().tolist()))
        foto_m = st.file_uploader("Foto Auto", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    s1, s2, s3 = st.columns(3)
    with s1: p_rca = st.selectbox("RCA", ["0 Euro", "250 Euro", "500 Euro"])
    with s2: p_kasko = st.selectbox("Danni/Kasko", ["0 Euro", "250 Euro", "500 Euro", "1000 Euro"])
    with s3:
        usa_g = st.checkbox("Pneumatici", value=True)
        g_tipo = st.radio("Tipo", ["ILLIMITATI", "A NUMERO"], horizontal=True) if usa_g else ""

    n1, n2, n3, n4 = st.columns(4)
    with n1: canone = st.number_input("Canone", value=500)
    with n2: anticipo = st.number_input("Anticipo", value=0)
    with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
    with n4: km = st.number_input("Km/Anno", value=15000)

    # --- GENERAZIONE PDF ---
    if st.button("✨ GENERA PREVENTIVO BIANCO"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(0, 0, 0) # Testo Nero di base
        
        # Data in Italiano
        data_it = datetime.now().strftime('%d %B %Y')
        pdf.set_y(58)
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 5, f"{data_it} - Offerta valida per {g_validita} giorni", align="C", ln=True)

        # Destinatario
        pdf.set_font(pdf.f_f, "B", 12)
        pdf.cell(0, 8, f"Spett.le {nome_cliente.upper()}", align="C", ln=True)

        # BLOCCO VEICOLO (SX) E FOTO (DX)
        y_pos = 80
        # Foto a destra
        f_path = "tmp.png"
        if foto_m:
            with open(f_path, "wb") as f: f.write(foto_m.getbuffer())
        else:
            f_path = f"foto_vetture/{marca.upper()}.jpg"
        
        if os.path.exists(f_path):
            pdf.image(f_path, 110, y_pos, 90)
        
        # Descrizione a sinistra (Eliminato Modello)
        pdf.set_xy(10, y_pos)
        pdf.set_font(pdf.f_f, "B", 20)
        pdf.multi_cell(95, 8, marca.upper())
        pdf.set_font(pdf.f_f, "", 11)
        pdf.multi_cell(95, 5, versione)
        
        pdf.ln(4)
        pdf.set_x(10)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.cell(95, 6, f"STATO: {t_veicolo.upper()}", ln=True)
        pdf.set_x(10)
        pdf.cell(95, 6, f"DURATA: {durata} Mesi", ln=True)
        pdf.set_x(10)
        pdf.cell(95, 6, f"PERCORRENZA: {km:,} km/anno".replace(",", "."), ln=True)

        # Servizi (Centrati)
        pdf.set_y(155)
        pdf.set_font(pdf.f_f, "B", 11)
        pdf.cell(0, 7, "SERVIZI INCLUSI NEL CANONE", ln=True, align="C")
        pdf.set_font(pdf.f_f, "", 10)
        
        servizi_txt = f"RCA (Franchigia {p_rca}) | Danni (Franchigia {p_kasko}) | Manutenzione Ord/Straord | Soccorso Stradale"
        if usa_g: servizi_txt += f" | Gomme {g_tipo}"
        
        pdf.multi_cell(0, 5, servizi_txt, align="C")
        
        # Disclaimer Foto
        pdf.ln(2)
        pdf.set_font(pdf.f_f, "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "*La foto del veicolo è puramente indicativa e potrebbe non riflettere l'allestimento scelto.", align="C", ln=True)

        # Canone Centrale
        pdf.set_y(210)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(pdf.f_f, "B", 28)
        pdf.cell(0, 15, f"EURO {canone}/MESE", align="C", ln=True)
        pdf.set_font(pdf.f_f, "B", 14)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo} (IVA Esclusa)", align="C", ln=True)

        # BARRA INFERIORE NERA PER CONSULENTE
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(0, 260, 210, 37, 'F')
        
        pdf.set_y(265)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.cell(0, 6, f"Consulente: {nome_cons}", align="C", ln=True)
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 5, f"E-mail: {email_cons} | Tel: {tel_cons}", align="C", ln=True)
        pdf.set_font(pdf.f_f, "I", 7)
        pdf.cell(0, 8, "Maldarizzi Rent - https://noleggio.maldarizzi.com/", align="C", ln=True)

        pdf.output("preventivo_white.pdf")
        st.success("Preventivo generato in formato Bianco & Nero!")
        with open("preventivo_white.pdf", "rb") as f:
            st.download_button("📩 SCARICA PREVENTIVO", f, f"Preventivo_{marca}.pdf")
