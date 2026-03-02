import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- 1. FUNZIONE LOGIN (CORRETTA) ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("""
            <style>
            .stApp { background-color: #000000; }
            </style>
            """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if os.path.exists("logo.png"):
                st.image("logo.png", width=200)
            else:
                st.title("MALDARIZZI RENT")
                
            st.subheader("Area Riservata Commerciale")
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

# --- ESECUZIONE APP ---
if check_password():

    # --- 2. CLASSE PDF "CAMILLO STYLE" ---
    class MaldarizziPDF(FPDF):
        def header(self):
            # Sfondo nero totale come richiesto
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 297, 'F')
            
            if os.path.exists("logo.png"):
                self.image("logo.png", 10, 10, 45)
            
            # Titolo "IL TUO PREVENTIVO" a destra
            self.set_font("Arial", "B", 35)
            self.set_text_color(255, 255, 255)
            self.set_xy(100, 20)
            self.multi_cell(100, 12, "IL TUO\nPREVENTIVO", align="R")
            self.ln(20)

        def footer(self):
            self.set_y(-20)
            self.set_font("Arial", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, "https://noleggio.maldarizzi.com/ - Offerta soggetta ad approvazione", 0, 0, "C")

    # --- 3. LOGICA APPLICATIVA ---
    st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
    
    NOME_FILE_FISSO = "dati.xlsx"
    
    if os.path.exists(NOME_FILE_FISSO):
        excel = pd.ExcelFile(NOME_FILE_FISSO)
        foglio = st.sidebar.selectbox("Seleziona Categoria", excel.sheet_names)
        df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
        df.columns = df.columns.str.strip()
    else:
        st.error("Caricare il file dati.xlsx nella cartella principale.")
        st.stop()

    # Dati Consulente
    st.sidebar.markdown("---")
    nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
    email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
    tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

    # Interfaccia Input
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        note = st.text_area("Note aggiuntive")
    
    with c2:
        st.subheader("🚘 Veicolo")
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
        modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
        versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
        foto_manuale = st.file_uploader("Foto Auto Personalizzata", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    n1, n2, n3, n4 = st.columns(4)
    with n1: canone = st.number_input("Canone Mensile (Euro)", value=500)
    with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
    with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
    with n4: km = st.number_input("Km/Anno", value=15000)

    # Generazione PDF
    if st.button("✨ GENERA PREVENTIVO PREMIUM"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255)
        
        # Data e Validità
        data_oggi = datetime.now().strftime("%d %B %Y")
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(10, 55)
        pdf.cell(0, 10, f"{data_oggi} Validità 7 giorni", ln=True)
        
        # Testo Benvenuto
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{nome_cliente},", ln=True)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 5, "di seguito trova il preventivo che meglio si adatta alle sue esigenze.\n")

        # Foto Auto
        foto_path = None
        if foto_manuale:
            with open("tmp.png", "wb") as f: f.write(foto_manuale.getbuffer())
            foto_path = "tmp.png"
        else:
            for ext in [".jpg", ".png", ".jpeg"]:
                p = f"foto_vetture/{marca.upper()}{ext}"
                if os.path.exists(p): foto_path = p; break
        
        if foto_path:
            pdf.image(foto_path, 10, 90, 110)
            pdf.set_y(160)
        else:
            pdf.ln(20)

        # Dettagli Veicolo
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 12, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font("Arial", "", 14)
        pdf.multi_cell(0, 7, versione)
        
        # Parametri
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 7, f"Durata contratto: {durata} Mesi", ln=True)
        pdf.cell(0, 7, f"Km/anno: {km:,} km".replace(",", "."), ln=True)

        # Prezzo e Anticipo
        pdf.set_y(230)
        pdf.set_font("Arial", "B", 22)
        pdf.cell(0, 15, f"Euro {canone}/mese (iva esclusa)", ln=True)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Anticipo: Euro {anticipo}", ln=True)

        # Disclaimer
        pdf.set_y(250)
        pdf.set_font("Arial", "I", 7)
        pdf.set_text_color(200, 200, 200)
        pdf.multi_cell(0, 4, "Attenzione: le foto ed il colore della vettura presenti in questa scheda sono puramente indicativi e non hanno valore contrattuale.")

        # Footer Consulente
        pdf.set_y(265)
        pdf.set_x(120)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(255,255,255)
        pdf.cell(0, 5, f"Consulente: {nome_cons}", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_x(120)
        pdf.cell(0, 5, f"Email: {email_cons}", ln=True)
        pdf.set_x(120)
        pdf.cell(0, 5, f"Tel: {tel_cons}", ln=True)

        pdf.output("preventivo.pdf")

        # Pioggia di Auto
        st.markdown("""
            <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
                <style>
                    @keyframes fall { 0% { transform: translateY(-10vh); opacity: 1; } 100% { transform: translateY(110vh); opacity: 0; } }
                    .car { position: absolute; font-size: 40px; animation: fall 2s linear forwards; }
                </style>
                <div class="car" style="left: 10%;">🚗</div><div class="car" style="left: 30%;">🚙</div><div class="car" style="left: 50%;">🚗</div><div class="car" style="left: 70%;">🚙</div><div class="car" style="left: 90%;">🚗</div>
            </div>""", unsafe_allow_html=True)

        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf")
