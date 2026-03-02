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
    # --- 2. CLASSE PDF "MALDARIZZI WHITE TEXT EDITION" ---
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
            # SFONDO DALL'IMMAGINE
            if os.path.exists("slider-maldarizzirent.jpg"):
                self.image("slider-maldarizzirent.jpg", 0, 0, 210, 297)
            else:
                self.set_fill_color(30, 30, 30) # Sfondo scuro di backup se manca immagine
                self.rect(0, 0, 210, 297, 'F')

            # BARRA SUPERIORE NERA
            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 40, 'F')
            if os.path.exists("logo.png"):
                self.image("logo.png", 75, 8, 60)
            
            self.set_y(45)
            self.set_font(self.f_f, "B", 20)
            self.set_text_color(255, 255, 255) # TESTO BIANCO
            self.cell(0, 10, "IL TUO PREVENTIVO", align="C", ln=True)

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Copilota", layout="wide")
    
    try: locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
    except: pass

    st.sidebar.header("📁 Database")
    uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino", type=["xlsx"])
    if uploaded_excel:
        with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
        st.sidebar.success("Database aggiornato!")

    if not os.path.exists("dati.xlsx"):
        st.error("Carica il file dati.xlsx")
        st.stop()

    excel = pd.ExcelFile("dati.xlsx")
    foglio = st.sidebar.selectbox("Seleziona Categoria", excel.sheet_names)
    df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
    
    st.sidebar.markdown("---")
    g_validita = st.sidebar.slider("Validità Offerta (gg)", 1, 30, 30)
    nome_cons = st.sidebar.text_input("Nome", "GRAZIA DEL VECCHIO")
    email_cons = st.sidebar.text_input("Email", "g.delvecchio@maldarizzi.com")
    tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", "Gentile CLIENTE")
        consegna = st.selectbox("Luogo Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
        note_p = st.text_area("Note e optional", height=70)
    with c2:
        st.subheader("🚘 Veicolo")
        t_veicolo = st.radio("Stato", ["Nuovo", "Usato"], horizontal=True)
        marca = st.selectbox("Marca", sorted(df['Brand Description'].unique().tolist()))
        modello_f = st.selectbox("Modello (Filtro)", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique().tolist()))
        versione = st.selectbox("Versione/Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello_f)]['Jato Product Description'].unique().tolist()))
        foto_m = st.file_uploader("Foto Auto", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    st.subheader("🛡️ Servizi e Penali")
    s1, s2, s3 = st.columns(3)
    with s1:
        p_rca = st.selectbox("Penale RCA", ["0 Euro", "250 Euro", "500 Euro"])
        p_if = st.selectbox("Penale Incendio/Furto", ["0%", "5%", "10%", "250 Euro"])
    with s2:
        p_kasko = st.selectbox("Penale Danni/Kasko", ["0 Euro", "250 Euro", "500 Euro", "1000 Euro"])
        infort = st.checkbox("Infortunio Conducente (PAI)", value=True)
    with s3:
        usa_gomme = st.checkbox("Pneumatici Inclusi?", value=True)
        g_num = "ILLIMITATE"
        if usa_gomme:
            g_tipo = st.radio("Tipo Gomme", ["ILLIMITATE", "A NUMERO"], horizontal=True)
            if g_tipo == "A NUMERO":
                g_num = st.number_input("N. Gomme", value=4, min_value=1)
        else:
            g_num = None

    st.markdown("---")
    st.subheader("💸 Dati Economici")
    n1, n2, n3, n4 = st.columns(4)
    with n1: canone = st.number_input("Canone/Mese (Euro)", value=500)
    with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
    with n3: durata = st.selectbox("Durata (Mesi)", [24, 36, 48, 60], index=1)
    with n4: km = st.number_input("Km/Anno", value=15000)

    # --- GENERAZIONE PDF ---
    if st.button("🚀 GENERA PREVENTIVO"):
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255) # SETTA TUTTO IL TESTO IN BIANCO
        
        # Data
        data_it = datetime.now().strftime('%d %B %Y').upper()
        pdf.set_y(58)
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 5, f"{data_it} - VALIDITÀ {g_validita} GIORNI", align="C", ln=True)
        pdf.set_font(pdf.f_f, "B", 12)
        pdf.cell(0, 8, f"SPETT.LE {nome_cliente.upper()}", align="C", ln=True)

        # BLOCCO VEICOLO (SX) E FOTO (DX)
        y_pos = 85
        f_path = "tmp.png"
        if foto_m:
            with open(f_path, "wb") as f: f.write(foto_m.getbuffer())
        else:
            f_path = f"foto_vetture/{marca.upper()}.jpg"
        
        if os.path.exists(f_path):
            pdf.image(f_path, 110, y_pos, 90)
        
        pdf.set_xy(15, y_pos)
        pdf.set_font(pdf.f_f, "B", 20)
        pdf.multi_cell(90, 8, marca.upper())
        pdf.set_x(15)
        pdf.set_font(pdf.f_f, "", 11)
        pdf.multi_cell(90, 5, versione)
        
        pdf.ln(4)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.set_x(15)
        pdf.cell(90, 6, f"STATO: {t_veicolo.upper()} ({consegna})", ln=True)
        pdf.set_x(15)
        pdf.cell(90, 6, f"DURATA CONTRATTO: {durata} MESI", ln=True)
        pdf.set_x(15)
        pdf.cell(90, 6, f"KM/ANNO: {km:,} KM".replace(",", "."), ln=True)

        # SERVIZI
        pdf.set_y(155)
        pdf.set_font(pdf.f_f, "B", 11)
        pdf.cell(0, 7, "SERVIZI INCLUSI NEL CANONE", ln=True, align="C")
        pdf.set_font(pdf.f_f, "", 9)
        
        serv_list = [
            f"RCA (Franchigia {p_rca})", 
            f"Incendio/Furto (Franchigia {p_if})",
            f"Danni/Kasko (Franchigia {p_kasko})",
            "Manutenzione Ordinaria/Straordinaria",
            "Assistenza Stradale H24"
        ]
        if g_num: serv_list.append(f"Gomme: {g_num}")
        if infort: serv_list.append("Infortunio Conducente (PAI)")
        
        pdf.multi_cell(0, 5, " | ".join(serv_list), align="C")
        
        # Disclaimer
        pdf.ln(2)
        pdf.set_font(pdf.f_f, "I", 8)
        pdf.set_text_color(200, 200, 200) # Grigio molto chiaro per il disclaimer
        pdf.cell(0, 5, "*Le immagini sono puramente indicative e non costituiscono vincolo contrattuale.", align="C", ln=True)

        # PREZZO
        pdf.set_y(210)
        pdf.set_text_color(255, 255, 255) # Riconferma Bianco
        pdf.set_font(pdf.f_f, "B", 28)
        pdf.cell(0, 15, f"EURO {canone}/MESE", align="C", ln=True)
        pdf.set_font(pdf.f_f, "B", 14)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo} (Iva Esclusa)", align="C", ln=True)

        if note_p:
            pdf.ln(2)
            pdf.set_font(pdf.f_f, "I", 9)
            pdf.multi_cell(0, 5, f"Note: {note_p}", align="C")

        # BARRA INFERIORE NERA
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(0, 260, 210, 37, 'F')
        
        pdf.set_y(265)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(pdf.f_f, "B", 10)
        pdf.cell(0, 6, f"CONSULENTE: {nome_cons.upper()}", align="C", ln=True)
        pdf.set_font(pdf.f_f, "", 9)
        pdf.cell(0, 5, f"E-mail: {email_cons} | Tel: {tel_cons}", align="C", ln=True)
        pdf.set_font(pdf.f_f, "I", 7)
        pdf.cell(0, 8, "MALDARIZZI RENT - HTTPS://NOLEGGIO.MALDARIZZI.COM/", align="C", ln=True)

        pdf.output("preventivo.pdf")
        st.success("Preventivo Generato con testo Bianco!")
        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA", f, f"Offerta_{marca}.pdf", key=f"dl_{datetime.now().timestamp()}")
