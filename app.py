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
    # --- 2. CLASSE PDF COMPATTA (SINGOLA PAGINA) ---
    class MaldarizziPDF(FPDF):
        def __init__(self):
            super().__init__()
            # Margini stretti per far stare tutto
            self.set_margins(10, 10, 10)
            self.set_auto_page_break(False) 
            if os.path.exists("Rubik-Light.ttf"):
                self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
            if os.path.exists("Rubik-Bold.ttf"):
                self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
            self.font_f = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

        def header(self):
            # Sfondo Nero Header (altezza ridotta)
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 35, 'F')
            if os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, 35)
            self.set_font(self.font_f, "B", 22)
            self.set_text_color(255, 255, 255)
            self.set_xy(100, 12)
            self.multi_cell(100, 8, "IL TUO\nPREVENTIVO", align="R")

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
    
    # Sidebar
    st.sidebar.header("⚙️ Impostazioni")
    giorni_validita = st.sidebar.slider("Validità (Giorni)", 1, 30, 30)
    
    if os.path.exists("dati.xlsx"):
        excel = pd.ExcelFile("dati.xlsx")
        foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
        df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
        df.columns = df.columns.str.strip()
    else:
        st.error("File dati.xlsx mancante!")
        st.stop()

    st.sidebar.markdown("---")
    nome_cons = st.sidebar.text_input("Consulente", "GRAZIA DEL VECCHIO")
    email_cons = st.sidebar.text_input("Email", "g.delvecchio@maldarizzi.com")
    tel_cons = st.sidebar.text_input("Telefono", "080 5322212")

    # Input Campi
    c1, c2 = st.columns(2)
    with c1:
        nome_cliente = st.text_input("Cliente", "CORALLO ANDREA")
        note = st.text_area("Note e Optional", height=60)
    with c2:
        t_veicolo = st.radio("Stato", ["Nuovo", "Usato"], horizontal=True)
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
        modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
        versione = st.selectbox("Versione", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
        foto_manuale = st.file_uploader("Cambia Foto", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    s1, s2, s3, s4 = st.columns(4)
    with s1: canone = st.number_input("Canone/Mese", value=500)
    with s2: anticipo = st.number_input("Anticipo", value=0)
    with s3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
    with s4: km = st.number_input("Km/Anno", value=15000)

    # --- GENERAZIONE PDF ---
    if st.button("✨ GENERA PREVENTIVO PAGINA SINGOLA"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        f_fam = pdf.font_f
        
        # Info Cliente e Data
        pdf.set_y(40)
        pdf.set_font(f_fam, "", 9)
        pdf.set_text_color(50, 50, 50)
        data_f = f"{datetime.now().strftime('%d/%B/%Y')} | Validità {giorni_validita} giorni"
        pdf.cell(0, 5, data_f, ln=True, align="R")
        
        pdf.set_font(f_fam, "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Spett.le {nome_cliente.upper()}", ln=True)

        # Immagine Auto (più piccola per risparmiare spazio)
        foto_path = "tmp_car.png"
        if foto_manuale:
            with open(foto_path, "wb") as f: f.write(foto_manuale.getbuffer())
        else:
            foto_path = f"foto_vetture/{marca.upper()}.jpg"
        
        if os.path.exists(foto_path):
            pdf.image(foto_path, 10, 65, 95)
            y_dopo_foto = 135
        else:
            y_dopo_foto = 70

        # Dettaglio Veicolo
        pdf.set_y(y_dopo_foto)
        pdf.set_font(f_fam, "B", 20)
        pdf.cell(0, 10, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font(f_fam, "", 10)
        pdf.multi_cell(0, 5, versione)
        
        # Parametri Tecnici (In riga)
        pdf.ln(2)
        pdf.set_font(f_fam, "B", 10)
        pdf.cell(50, 7, f"Durata: {durata} Mesi")
        pdf.cell(50, 7, f"Km/Anno: {km:,}".replace(",", "."))
        pdf.cell(0, 7, f"Stato: {t_veicolo.upper()}", ln=True)

        # Servizi (Box grigio compatto)
        pdf.ln(2)
        pdf.set_fill_color(240, 240, 240)
        pdf.rect(10, pdf.get_y(), 190, 30, 'F')
        pdf.set_font(f_fam, "B", 9)
        pdf.cell(0, 6, "  SERVIZI INCLUSI:", ln=True)
        pdf.set_font(f_fam, "", 8)
        pdf.cell(90, 4, "  - RCA e Kasko (penali incluse)", ln=0)
        pdf.cell(90, 4, "- Manutenzione Ordinaria/Straordinaria", ln=1)
        pdf.cell(90, 4, "  - Incendio e Furto", ln=0)
        pdf.cell(90, 4, "- Assistenza Stradale H24", ln=1)
        pdf.cell(90, 4, "  - Tassa Proprietà", ln=0)
        pdf.cell(90, 4, "- Infortunio Conducente", ln=1)

        # Prezzo (Box Nero)
        pdf.set_y(195)
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(10, 195, 190, 20, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(f_fam, "B", 22)
        pdf.cell(0, 20, f"EURO {canone}/MESE (IVA ESCLUSA)", align="C", ln=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(f_fam, "B", 12)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo}", align="C", ln=True)

        # Note
        if note:
            pdf.set_font(f_fam, "I", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 4, f"Note: {note}")

        # Footer e Contatti (Bloccati in fondo alla pagina)
        pdf.set_y(260)
        pdf.set_font(f_fam, "B", 9)
        pdf.cell(0, 5, f"Consulente: {nome_cons}", ln=True, align="R")
        pdf.set_font(f_fam, "", 8)
        pdf.cell(0, 4, f"E-mail: {email_cons}", ln=True, align="R")
        pdf.cell(0, 4, f"Tel: {tel_cons}", ln=True, align="R")
        
        pdf.set_y(278)
        pdf.set_font(f_fam, "I", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, "Maldarizzi Rent - https://noleggio.maldarizzi.com/", 0, 0, "C")

        pdf.output("preventivo_fisso.pdf")
        
        st.success("Preventivo generato correttamente in 1 pagina!")
        with open("preventivo_fisso.pdf", "rb") as f:
            st.download_button("📩 SCARICA PREVENTIVO", f, f"Offerta_{modello}.pdf", key="dl_one_page")
