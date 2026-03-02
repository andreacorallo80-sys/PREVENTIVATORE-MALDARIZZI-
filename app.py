import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

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
    # --- 2. CLASSE PDF "ROAD EDITION" ---
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
            # Sfondo Nero Totale
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 297, 'F')
            
            # Decorazione "Strada" laterale (ispirata a COPILOTA.jpg)
            self.set_draw_color(255, 255, 255)
            self.set_line_width(0.5)
            # Disegno di linee curve/strada stilizzate sul lato sinistro
            self.line(5, 50, 5, 250)
            self.line(8, 60, 8, 240)
            
            if os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, 45)
            
            # Titolo a destra
            self.set_font(self.f_f, "B", 35)
            self.set_text_color(255, 255, 255)
            self.set_xy(100, 15)
            self.multi_cell(100, 11, "IL TUO\nPREVENTIVO", align="R")

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
    
    st.sidebar.header("⚙️ Impostazioni")
    g_validita = st.sidebar.slider("Giorni Validità", 1, 30, 30)
    
    if os.path.exists("dati.xlsx"):
        excel = pd.ExcelFile("dati.xlsx")
        foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
        df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
    else:
        st.error("Manca dati.xlsx")
        st.stop()

    st.sidebar.markdown("---")
    nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
    email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
    tel_cons = st.sidebar.text_input("Tel", "080 5322212")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        note = st.text_area("Note e Optional")
    with c2:
        st.subheader("🚘 Veicolo")
        t_veicolo = st.radio("Stato", ["Nuovo", "Usato"], horizontal=True)
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
        modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
        versione = st.selectbox("Versione", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
        foto_m = st.file_uploader("Foto", type=["jpg","png","jpeg"])

    st.markdown("---")
    # ICONA AGGIORNATA: 🛠️ Servizi e Penali
    st.subheader("🛠️ Servizi e Penali")
    s1, s2, s3 = st.columns(3)
    with s1: p_rca = st.selectbox("RCA", ["0 Euro", "250 Euro", "500 Euro"])
    with s2: p_kasko = st.selectbox("Danni/Kasko", ["0 Euro", "250 Euro", "500 Euro", "1000 Euro"])
    with s3:
        usa_g = st.checkbox("Pneumatici", value=True)
        g_tipo = st.radio("Tipo", ["ILLIMITATI", "A NUMERO"], horizontal=True) if usa_g else ""

    st.markdown("---")
    # ICONA AGGIORNATA: 💸 Dati Economici
    st.subheader("💸 Dati Economici")
    n1, n2, n3, n4 = st.columns(4)
    with n1: canone = st.number_input("Canone/Mese", value=500)
    with n2: anticipo = st.number_input("Anticipo", value=0)
    with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
    with n4: km = st.number_input("Km/Anno", value=15000)

    # --- GENERAZIONE PDF ---
    if st.button("🚀 GENERA PREVENTIVO"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255)
        
        # Data e Intro
        pdf.set_xy(15, 45)
        pdf.set_font(pdf.f_f, "", 10)
        pdf.cell(0, 5, f"{datetime.now().strftime('%d %B %Y')} Validità {g_validita} giorni", ln=True)
        pdf.ln(2)
        pdf.set_font(pdf.f_f, "B", 14)
        pdf.cell(0, 8, f"{nome_cliente.upper()},", ln=True)
        pdf.set_font(pdf.f_f, "", 10)
        pdf.cell(0, 5, "di seguito trova il preventivo che meglio si adatta alle sue esigenze.", ln=True)

        # Foto Auto (Spostata leggermente per far spazio alla strada decorativa)
        f_path = "tmp.png"
        if foto_m:
            with open(f_path, "wb") as f: f.write(foto_m.getbuffer())
        else:
            f_path = f"foto_vetture/{marca.upper()}.jpg"
        
        if os.path.exists(f_path):
            pdf.image(f_path, 15, 75, 105)
            pdf.set_y(150)
        else:
            pdf.set_y(90)

        # Info Veicolo
        pdf.set_font(pdf.f_f, "B", 24)
        pdf.set_x(15)
        pdf.cell(0, 12, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font(pdf.f_f, "", 11)
        pdf.set_x(15)
        pdf.multi_cell(0, 5, versione)
        
        pdf.ln(5)
        pdf.set_font(pdf.f_f, "B", 11)
        pdf.set_x(15)
        pdf.cell(0, 6, f"Durata contratto: {durata} Mesi", ln=True)
        pdf.set_x(15)
        pdf.cell(0, 6, f"Km/anno: {km:,} km".replace(",", "."), ln=True)

        # SPOSTAMENTO SERVIZI SULLA DESTRA
        pdf.set_xy(120, 155) # Posiziona il cursore a destra
        pdf.set_font(pdf.f_f, "B", 11)
        pdf.cell(0, 7, "SERVIZI INCLUSI:", ln=True, align="L")
        pdf.set_font(pdf.f_f, "", 10)
        
        servizi = [
            f"RCA: franchigia {p_rca}", 
            f"Danni: franchigia {p_kasko}", 
            "Manutenzione Ord/Straord", 
            "Assistenza Stradale H24",
            "Tassa di Proprieta"
        ]
        if usa_g: servizi.append(f"Gomme: {g_tipo}")
        
        for s in servizi:
            pdf.set_x(120)
            pdf.cell(0, 5, f"- {s}", ln=True, align="L")

        # Canone e Anticipo
        pdf.set_y(225)
        pdf.set_font(pdf.f_f, "B", 24)
        pdf.cell(0, 15, f"EURO {canone}/MESE (IVA ESCLUSA)", ln=True, align="L")
        pdf.set_font(pdf.f_f, "B", 14)
        pdf.cell(0, 10, f"Anticipo: Euro {anticipo}", ln=True, align="L")

        # Footer e Disclaimer
        pdf.set_y(255)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.cell(0, 6, f"TIPOLOGIA VEICOLO: {t_veicolo.upper()}", ln=True, align="R")
        
        pdf.set_font(pdf.f_f, "", 7)
        pdf.set_text_color(180, 180, 180)
        pdf.multi_cell(0, 3, "Le immagini sono puramente indicative. Offerta valida salvo approvazione. https://noleggio.maldarizzi.com/")

        # Contatti Consulente
        pdf.set_y(270)
        pdf.set_x(120)
        pdf.set_font(pdf.f_f, "B", 9)
        pdf.set_text_color(255,255,255)
        pdf.cell(0, 4, f"Consulente: {nome_cons}", ln=True, align="R")
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 4, f"Email: {email_cons}", ln=True, align="R")
        pdf.cell(0, 4, f"Tel: {tel_cons}", ln=True, align="R")

        pdf.output("preventivo.pdf")
        st.success("PDF Generato con layout 'Road'!")
        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf", key=f"dl_{datetime.now().timestamp()}")
