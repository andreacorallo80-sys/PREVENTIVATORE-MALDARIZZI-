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
    # --- 2. CLASSE PDF "MALDARIZZI CENTERED" ---
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
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 297, 'F') # Sfondo Nero
            
            # 1. Logo al centro più visibile
            if os.path.exists("logo.png"):
                # Centrato: (210mm - 60mm larghezza logo) / 2 = 75
                self.image("logo.png", 75, 12, 60)
            
            # 2. Scritta IL TUO PREVENTIVO centrata e più piccola
            self.set_font(self.f_f, "B", 24)
            self.set_text_color(255, 255, 255)
            self.set_xy(0, 38)
            self.cell(210, 12, "IL TUO PREVENTIVO", align="C", ln=True)

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
    
    st.sidebar.header("📁 Gestione Listino")
    uploaded_excel = st.sidebar.file_uploader("Carica Excel", type=["xlsx"])
    if uploaded_excel:
        with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
        st.sidebar.success("Listino aggiornato!")

    if not os.path.exists("dati.xlsx"):
        st.error("Per favore, carica il file dati.xlsx")
        st.stop()

    excel = pd.ExcelFile("dati.xlsx")
    foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
    df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
    df.columns = df.columns.str.strip()

    st.sidebar.markdown("---")
    g_validita = st.sidebar.slider("Validità (giorni)", 1, 30, 30)
    nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
    email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
    tel_cons = st.sidebar.text_input("Telefono", "080 5322212")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        note_p = st.text_area("Note/Optional")
    with c2:
        st.subheader("🚘 Veicolo")
        t_veicolo = st.radio("Stato", ["Nuovo", "Usato"], horizontal=True)
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
        modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
        versione = st.selectbox("Versione", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
        foto_m = st.file_uploader("Foto Auto", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    st.subheader("🛠️ Servizi e Penali")
    s1, s2, s3 = st.columns(3)
    with s1:
        p_rca = st.selectbox("RCA", ["0 Euro", "250 Euro", "500 Euro"])
        p_if = st.selectbox("Incendio/Furto", ["0%", "5%", "10%", "250 Euro"])
    with s2:
        p_kasko = st.selectbox("Danni/Kasko", ["0 Euro", "250 Euro", "500 Euro", "1000 Euro"])
        infort = st.checkbox("Infortunio Conducente", value=True)
    with s3:
        usa_g = st.checkbox("Pneumatici?", value=True)
        g_tipo = st.radio("Tipo", ["ILLIMITATI", "A NUMERO"], horizontal=True) if usa_g else ""

    st.markdown("---")
    st.subheader("💸 Offerta")
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
        
        # Data e Intro (Centrate)
        pdf.set_y(55)
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 5, f"{datetime.now().strftime('%d %B %Y')} - Validità {g_validita} giorni", align="C", ln=True)
        pdf.set_font(pdf.f_f, "B", 12)
        pdf.cell(0, 8, f"Spett.le {nome_cliente.upper()}", align="C", ln=True)

        # BLOCCO CENTRALE: DESCRIZIONE A SX E FOTO A DX
        y_start_block = 75
        
        # Foto a destra
        f_path = "tmp.png"
        if foto_m:
            with open(f_path, "wb") as f: f.write(foto_m.getbuffer())
        else:
            f_path = f"foto_vetture/{marca.upper()}.jpg"
        
        if os.path.exists(f_path):
            pdf.image(f_path, 105, y_start_block, 95) # Foto a destra
        
        # Descrizione a sinistra
        pdf.set_xy(10, y_start_block)
        pdf.set_font(pdf.f_f, "B", 18)
        pdf.multi_cell(90, 8, f"{marca} {modello}".upper())
        pdf.set_font(pdf.f_f, "", 10)
        pdf.multi_cell(90, 5, versione)
        
        pdf.ln(3)
        pdf.set_x(10)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.cell(90, 6, f"STATO: {t_veicolo.upper()}", ln=True)
        pdf.set_x(10)
        pdf.cell(90, 6, f"DURATA: {durata} Mesi", ln=True)
        pdf.set_x(10)
        pdf.cell(90, 6, f"KM/ANNO: {km:,} km".replace(",", "."), ln=True)

        # SERVIZI INCLUSI (Sotto il blocco descrizione/foto)
        pdf.set_y(150)
        pdf.set_font(pdf.f_f, "B", 11)
        pdf.cell(0, 7, "SERVIZI INCLUSI NEL CANONE:", ln=True, align="C")
        pdf.set_font(pdf.f_f, "", 10)
        
        servizi = [
            f"RCA: franchigia {p_rca} | Incendio e Furto: {p_if}",
            f"Copertura Danni: franchigia {p_kasko} | Assistenza Stradale H24",
            "Manutenzione Ordinaria e Straordinaria | Tassa di Proprietà"
        ]
        if infort: servizi.append("Infortunio Conducente (PAI)")
        if usa_g: servizi.append(f"Gestione Pneumatici: {g_tipo}")
        
        for s in servizi:
            pdf.cell(0, 5, s, ln=True, align="C")

        # CANONE CENTRALE
        pdf.set_y(210)
        pdf.set_font(pdf.f_f, "B", 28)
        pdf.cell(0, 15, f"EURO {canone}/MESE (IVA ESCLUSA)", ln=True, align="C")
        pdf.set_font(pdf.f_f, "B", 16)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo}", ln=True, align="C")

        # NOTE (Se presenti)
        if note_p:
            pdf.ln(5)
            pdf.set_font(pdf.f_f, "I", 8)
            pdf.multi_cell(0, 4, f"Note: {note_p}", align="C")

        # CONSULENTE AL CENTRO
        pdf.set_y(260)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.cell(0, 5, f"Consulente: {nome_cons}", ln=True, align="C")
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 4, f"E-mail: {email_cons} | Tel: {tel_cons}", ln=True, align="C")
        
        pdf.set_y(278)
        pdf.set_font(pdf.f_f, "I", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, "Maldarizzi Rent - https://noleggio.maldarizzi.com/", 0, 0, "C")

        pdf.output("preventivo_maldarizzi.pdf")
        st.success("Preventivo Centrato Generato!")
        with open("preventivo_maldarizzi.pdf", "rb") as f:
            st.download_button("📩 SCARICA PREVENTIVO", f, f"Offerta_{modello}.pdf")
