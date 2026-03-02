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
    # --- 2. CLASSE PDF "ONE PAGE PREMIUM" ---
    class MaldarizziPDF(FPDF):
        def header(self):
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 297, 'F') # Sfondo Nero
            if os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, 40)
            self.set_font("Arial", "B", 30)
            self.set_text_color(255, 255, 255)
            self.set_xy(100, 15)
            self.multi_cell(100, 10, "IL TUO\nPREVENTIVO", align="R")

        def footer(self):
            self.set_y(-12)
            self.set_font("Arial", "I", 7)
            self.set_text_color(130, 130, 130)
            self.cell(0, 10, "https://noleggio.maldarizzi.com/ - Offerta soggetta ad approvazione", 0, 0, "C")

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
    
    # Sidebar: Gestione Dati, Consulente e Validità
    st.sidebar.header("⚙️ Impostazioni Offerta")
    giorni_validita = st.sidebar.slider("Giorni di Validità", 1, 30, 7)
    
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Database")
    uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
    if uploaded_excel:
        with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
        st.sidebar.success("Database aggiornato!")

    if not os.path.exists("dati.xlsx"):
        st.error("Carica dati.xlsx per procedere")
        st.stop()

    excel = pd.ExcelFile("dati.xlsx")
    foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
    df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
    df.columns = df.columns.str.strip()

    st.sidebar.markdown("---")
    st.sidebar.header("🤵 Consulente")
    nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
    email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
    tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

    # Layout Input Principale
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        consegna = st.selectbox("Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
        note = st.text_area("Note e optional", height=70)
    
    with c2:
        st.subheader("🚘 Veicolo")
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
        modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
        versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
        foto_manuale = st.file_uploader("Foto Personalizzata", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    st.subheader("🛡️ Servizi e Penali")
    s1, s2, s3 = st.columns(3)
    with s1:
        p_rca = st.selectbox("Penale RCA", ["0 Euro", "250 Euro", "500 Euro"])
        p_if = st.selectbox("Penale Incendio/Furto", ["0%", "5%", "10%", "250 Euro", "500 Euro"])
    with s2:
        p_kasko = st.selectbox("Penale Danni/Kasko", ["0 Euro", "250 Euro", "500 Euro", "1000 Euro"])
        infort = st.checkbox("Infortunio Conducente", value=True)
    with s3:
        usa_gomme = st.checkbox("Includere Servizio Pneumatici?", value=True)
        if usa_gomme:
            g_tipo = st.radio("Tipo Pneumatici", ["ILLIMITATI", "A NUMERO"], horizontal=True)
            g_num = st.number_input("N. Gomme", 4) if g_tipo == "A NUMERO" else "ILLIMITATI"

    st.markdown("---")
    n1, n2, n3, n4 = st.columns(4)
    with n1: canone = st.number_input("Canone (Euro)", value=500)
    with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
    with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
    with n4: km = st.number_input("Km/Anno", value=15000)

    # --- GENERAZIONE PDF ---
    if st.button("✨ GENERA PREVENTIVO"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255)
        
        # Intestazione Data e Validità Editabile
        data_f = f"{datetime.now().strftime('%d %B %Y')} Validita {giorni_validita} giorni"
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(10, 42)
        pdf.cell(0, 10, data_f, ln=True)
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{nome_cliente.upper()},", ln=True)
        pdf.set_font("Arial", "I", 9)
        pdf.multi_cell(0, 4, "di seguito trova il preventivo che meglio si adatta alle sue esigenze.")

        # Foto
        foto_path = None
        if foto_manuale:
            with open("tmp.png", "wb") as f: f.write(foto_manuale.getbuffer())
            foto_path = "tmp.png"
        else:
            for ext in [".jpg", ".png", ".jpeg"]:
                p = f"foto_vetture/{marca.upper()}{ext}"
                if os.path.exists(p): foto_path = p; break
        
        if foto_path:
            pdf.image(foto_path, 10, 65, 100)
            pdf.set_y(135)
        else:
            pdf.ln(10)

        # Dati Veicolo
        pdf.set_font("Arial", "B", 22)
        pdf.cell(0, 10, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 5, versione)
        
        # Blocchi Tecnici
        pdf.ln(3)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, f"Durata contratto: {durata} Mesi", ln=True)
        pdf.cell(0, 6, f"Km/anno: {km:,} km".replace(",", "."), ln=True)

        # Servizi su 2 colonne
        pdf.ln(3)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "SERVIZI INCLUSI:", ln=True)
        pdf.set_font("Arial", "", 9)
        
        serv_list = [
            f"- RCA: franchigia {p_rca}",
            f"- Incendio/Furto: franchigia {p_if}",
            f"- Danni: franchigia {p_kasko}",
            "- Manutenzione Ord/Straord",
            "- Assistenza Stradale H24"
        ]
        if infort: serv_list.append("- Infortunio Conducente")
        if usa_gomme:
            txt_g = f"- Gomme: {g_num}" if g_tipo == "A NUMERO" else "- Gomme: ILLIMITATE"
            serv_list.insert(3, txt_g) # Lo inserisce in quarta posizione
        
        y_serv = pdf.get_y()
        for i, s in enumerate(serv_list):
            if i < 4:
                pdf.cell(90, 5, s, ln=True)
            else:
                if i == 4: pdf.set_xy(110, y_serv)
                pdf.set_x(110)
                pdf.cell(90, 5, s, ln=True)

        # Prezzo
        pdf.set_y(225)
        pdf.set_font("Arial", "B", 26)
        pdf.cell(0, 12, f"Euro {canone}/mese (iva esclusa)", ln=True, align="L")
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Anticipo: Euro {anticipo}", ln=True, align="L")

        # Note e Disclaimer
        if note:
            pdf.set_font("Arial", "I", 8)
            pdf.set_text_color(180, 180, 180)
            pdf.multi_cell(0, 4, f"Note: {note}")

        pdf.set_y(255)
        pdf.set_font("Arial", "I", 7)
        pdf.set_text_color(180, 180, 180)
        pdf.multi_cell(0, 3, "Le immagini sono puramente indicative. Offerta valida salvo approvazione. I canoni possono variare in base alla quotazione della societa di noleggio al momento dell'ordine.")

        # Contatti Consulente
        pdf.set_y(270)
        pdf.set_x(120)
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(255,255,255)
        pdf.cell(0, 4, f"Consulente: {nome_cons}", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.set_x(120)
        pdf.cell(0, 4, f"Email: {email_cons}", ln=True)
        pdf.set_x(120)
        pdf.cell(0, 4, f"Tel: {tel_cons}", ln=True)

        pdf.output("preventivo.pdf")
        
        st.success("Preventivo Generato!")
        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf")
        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf")

