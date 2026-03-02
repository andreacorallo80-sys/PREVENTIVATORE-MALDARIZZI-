import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime, timedelta

# --- 1. GESTIONE LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("""
            <style>
            .stApp { background-color: #000000; }
            .login-box { background-color: #111; padding: 30px; border-radius: 10px; border: 1px solid #333; color: white; }
            </style>
            """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.image("logo.png", width=200) if os.path.exists("logo.png") else st.title("MALDARIZZI RENT")
            st.subheader("Aree Riservata Commerciale")
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
    # --- 2. CLASSE PDF "CAMILLO STYLE" ---
    class MaldarizziPDF(FPDF):
        def header(self):
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 297, 'F') # Sfondo nero totale
            if os.path.exists("logo.png"):
                self.image("logo.png", 10, 10, 45)
            
            # Titolo "IL TUO PREVENTIVO" a destra come nell'originale
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

    # --- 3. APP STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
    
    # Sidebar per database e consulente
    st.sidebar.image("logo.png") if os.path.exists("logo.png") else None
    st.sidebar.title("Area Gestionale")
    
    uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino Excel", type=["xlsx"])
    if uploaded_excel:
        with open("dati.xlsx", "wb") as f:
            f.write(uploaded_excel.getbuffer())
        st.sidebar.success("Database aggiornato!")

    if os.path.exists("dati.xlsx"):
        excel = pd.ExcelFile("dati.xlsx")
        foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
        df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
        df.columns = df.columns.str.strip()
    else:
        st.error("Manca dati.xlsx")
        st.stop()

    st.sidebar.markdown("---")
    nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
    email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
    tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

    # --- INPUT PREVENTIVO ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        consegna = st.selectbox("Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
        note = st.text_area("Note aggiuntive")
    
    with c2:
        st.subheader("🚘 Veicolo")
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
        modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
        versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
        foto_manuale = st.file_uploader("Foto Auto", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    s1, s2, s3 = st.columns(3)
    with s1:
        p_rca = st.selectbox("Penale RCA", ["0", "250"])
        p_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "5%", "10%"])
    with s2:
        p_kasko = st.selectbox("Penale Kasko", ["0", "250", "500", "1000", "2000"])
        infort = st.checkbox("Infortunio Conducente", value=True)
    with s3:
        g_tipo = st.radio("Gomme", ["ILLIMITATE", "A NUMERO"])
        g_num = st.number_input("N. Gomme", 4) if g_tipo == "A NUMERO" else "ILLIMITATE"

    st.markdown("---")
    n1, n2, n3, n4 = st.columns(4)
    with n1: canone = st.number_input("Canone Mensile (Euro)", value=500)
    with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
    with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
    with n4: km = st.number_input("Km/Anno", value=15000)

    # --- GENERAZIONE PDF ---
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
        
        # Parametri Tecnici
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 7, f"Durata contratto: {durata} Mesi", ln=True)
        pdf.cell(0, 7, f"Km/anno: {km:,} km".replace(",", "."), ln=True)
        
        # Servizi (due colonne)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Servizi inclusi:", ln=True)
        pdf.set_font("Arial", "", 10)
        servizi = [
            f"RCA: franchigia Euro {p_rca}",
            f"Incendio e furto: franchigia {p_if}",
            f"Copertura Danni: franchigia Euro {p_kasko}",
            f"Gomme: {g_num}",
            "MANUTENZIONE ORDINARIA E STRAORDINARIA",
            "TRAINO E ASSISTENZA STRADALE"
        ]
        if infort: servizi.append("INFORTUNIO CONDUCENTE")
        for s in servizi:
            pdf.cell(0, 5, f"- {s}", ln=True)

        # Disclaimer
        pdf.ln(5)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(200, 200, 200)
        pdf.multi_cell(0, 4, "Attenzione: le foto ed il colore della vettura presenti in questa scheda, è puramente indicativa e non ha valore contrattuale.")

        # Prezzo e Anticipo
        pdf.set_y(240)
        pdf.set_font("Arial", "B", 22)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 15, f"Euro {canone}/mese (iva esclusa)", ln=True)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Anticipo: Euro {anticipo}", ln=True)

        # Footer Consulente
        pdf.set_y(260)
        pdf.set_x(120)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, f"Consulente: {nome_cons}", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_x(120)
        pdf.cell(0, 5, f"Email: {email_cons}", ln=True)
        pdf.set_x(120)
        pdf.cell(0, 5, f"Tel: {tel_cons}", ln=True)

        pdf.output("preventivo.pdf")

        # --- PIOGGIA DI AUTO ---
        st.markdown("""
            <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
                <style>
                    @keyframes fall { 0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; } 100% { transform: translateY(110vh) rotate(360deg); opacity: 0; } }
                    .car { position: absolute; font-size: 40px; animation: fall linear forwards; }
                </style>
                """ + "".join([f'<div class="car" style="left: {i*8}%; animation-duration: {1.5+(i%2)}s; animation-delay: {i*0.1}s;">🚗</div>' for i in range(12)]) + """
            </div>""", unsafe_allow_html=True)

        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf")
