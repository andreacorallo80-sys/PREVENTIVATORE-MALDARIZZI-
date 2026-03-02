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
    # --- 2. CLASSE PDF "MALDARIZZI ONE PAGE" ---
    class MaldarizziPDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_margins(10, 10, 10)
            self.set_auto_page_break(False) # Forza la singola pagina
            if os.path.exists("Rubik-Light.ttf"):
                self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
            if os.path.exists("Rubik-Bold.ttf"):
                self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
            self.font_family_custom = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

        def header(self):
            # Sfondo nero totale come richiesto
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 297, 'F') 
            
            if os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, 45)
            
            # Titolo "IL TUO PREVENTIVO" a destra
            self.set_font(self.font_family_custom, "B", 32)
            self.set_text_color(255, 255, 255)
            self.set_xy(100, 15)
            self.multi_cell(100, 11, "IL TUO\nPREVENTIVO", align="R")

        def footer(self):
            self.set_y(-12)
            self.set_font(self.font_family_custom, "", 7)
            self.set_text_color(130, 130, 130)
            self.cell(0, 10, "maldarizzi.com | Offerta soggetta ad approvazione", 0, 0, "C")

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
    
    st.sidebar.header("⚙️ Impostazioni Offerta")
    giorni_validita = st.sidebar.slider("Giorni di Validità", 1, 30, 30)
    
    st.sidebar.markdown("---")
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

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        consegna = st.selectbox("Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
        note = st.text_area("Note e optional", height=70)
    
    with c2:
        st.subheader("🚘 Veicolo")
        t_veicolo = st.radio("Stato Veicolo", ["Nuovo", "Usato"], horizontal=True)
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

    if st.button("✨ GENERA PREVENTIVO"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        f_fam = pdf.font_family_custom
        pdf.set_text_color(255, 255, 255)
        
        # Data e Validità
        data_f = f"{datetime.now().strftime('%d %B %Y')} Validita {giorni_validita} giorni"
        pdf.set_font(f_fam, "", 10)
        pdf.set_xy(10, 45)
        pdf.cell(0, 10, data_f, ln=True)
        
        pdf.set_font(f_fam, "", 12)
        pdf.cell(0, 8, f"{nome_cliente.upper()},", ln=True)
        pdf.set_font(f_fam, "", 9) 
        pdf.multi_cell(0, 4, "di seguito trova il preventivo che meglio si adatta alle sue esigenze.")

        # Foto (Dimensionata per stare in una pagina)
        foto_path = None
        if foto_manuale:
            with open("tmp.png", "wb") as f: f.write(foto_manuale.getbuffer())
            foto_path = "tmp.png"
        else:
            for ext in [".jpg", ".png", ".jpeg", ".JPG"]:
                p = f"foto_vetture/{marca.upper()}{ext}"
                if os.path.exists(p): foto_path = p; break
        
        if foto_path:
            pdf.image(foto_path, 10, 70, 100)
            pdf.set_y(140)
        else:
            pdf.set_y(80)

        # Dati Veicolo
        pdf.set_font(f_fam, "B", 24)
        pdf.cell(0, 12, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font(f_fam, "", 12)
        pdf.multi_cell(0, 6, versione)
        
        # Parametri Tecnici
        pdf.ln(4)
        pdf.set_font(f_fam, "B", 11)
        pdf.cell(0, 6, f"Durata contratto: {durata} Mesi", ln=True)
        pdf.cell(0, 6, f"Km/anno: {km:,} km".replace(",", "."), ln=True)

        # Servizi su due colonne
        pdf.ln(4)
        pdf.set_font(f_fam, "B", 11)
        pdf.cell(0, 7, "SERVIZI INCLUSI:", ln=True)
        pdf.set_font(f_fam, "", 10)
        
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
            serv_list.insert(3, txt_g)
        
        y_serv = pdf.get_y()
        for i, s in enumerate(serv_list):
            # Pulizia testo per evitare crash Unicode
            s_clean = s.encode('latin-1', 'replace').decode('latin-1')
            if i < 4:
                pdf.cell(90, 6, s_clean, ln=True)
            else:
                if i == 4: pdf.set_xy(110, y_serv)
                pdf.set_x(110)
                pdf.cell(90, 6, s_clean, ln=True)

        # Prezzo (Box Black Style)
        pdf.set_y(225)
        pdf.set_font(f_fam, "B", 26)
        pdf.cell(0, 14, f"Euro {canone}/mese (iva esclusa)", ln=True, align="L")
        pdf.set_font(f_fam, "B", 16)
        pdf.cell(0, 10, f"Anticipo: Euro {anticipo}", ln=True, align="L")

        # Footer e Disclaimer
        pdf.set_y(255)
        pdf.set_font(f_fam, "B", 10)
        pdf.cell(0, 6, f"TIPOLOGIA VEICOLO: {t_veicolo.upper()}", ln=True, align="R")
        
        pdf.set_font(f_fam, "", 7)
        pdf.set_text_color(180, 180, 180)
        pdf.multi_cell(0, 3, "Le immagini sono puramente indicative. Offerta valida salvo approvazione. I canoni possono variare in base alla quotazione della societa di noleggio al momento dell'ordine.")

        # Consulente
        pdf.set_y(270)
        pdf.set_x(120)
        pdf.set_font(f_fam, "B", 10)
        pdf.set_text_color(255,255,255)
        pdf.cell(0, 4, f"Consulente: {nome_cons}", ln=True)
        pdf.set_font(f_fam, "", 9)
        pdf.set_x(120)
        pdf.cell(0, 4, f"Email: {email_cons}", ln=True)
        pdf.set_x(120)
        pdf.cell(0, 4, f"Tel: {tel_cons}", ln=True)

        pdf.output("preventivo.pdf")
        
        st.success("Preventivo Generato!")
        with open("preventivo.pdf", "rb") as f:
            st.download_button(
                label="📩 SCARICA IL PREVENTIVO",
                data=f,
                file_name=f"Offerta_{modello}.pdf",
                key=f"dl_btn_{datetime.now().timestamp()}"
            )
