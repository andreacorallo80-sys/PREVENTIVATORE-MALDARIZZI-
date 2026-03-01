import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF PROFESSIONALE BLACK EDITION ---
class MaldarizziPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 297, 'F')
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 10, 45)
        self.ln(30)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "https://noleggio.maldarizzi.com/ - Documento ad uso interno commerciale", 0, 0, "C")

# --- APP STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Rent - Pro", layout="wide")
st.title("🚀 Maldarizzi Rent - Preventivatore Professionale")

# --- GESTIONE FILE MODELLI (AGGIORNABILE) ---
st.sidebar.header("📁 Gestione Database")
uploaded_file = st.sidebar.file_uploader("Aggiorna listino Excel", type=["xlsx"])
NOME_FILE_FISSO = "dati.xlsx"

if uploaded_file is not None:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("Database aggiornato!")

if not os.path.exists(NOME_FILE_FISSO):
    st.error("Carica il file dati.xlsx per iniziare.")
    st.stop()

# Caricamento Dati
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# --- INPUT COMMERCIALI ---
st.sidebar.header("🤵 Consulente")
nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")

# --- LAYOUT PRINCIPALE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Cliente e Consegna")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.radio("Modalità di Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
    foto_vettura = st.file_uploader("🖼️ Foto Vettura", type=["jpg", "png", "jpeg"])

with col2:
    st.subheader("🚘 Selezione Auto")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))

st.markdown("---")
st.subheader("🛡️ Servizi e Penali")
s1, s2, s3 = st.columns(3)
with s1:
    penale_rca = st.selectbox("Penale RCA (€)", ["0", "250"])
with s2:
    penale_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "0%", "5%", "10%", "20%"])
with s3:
    penale_kasko = st.selectbox("Penale Kasko (Danni) (€)", ["0", "250", "500", "1000", "2000"])

st.markdown("---")
st.subheader("💰 Parametri Noleggio")
n1, n2, n3, n4 = st.columns(4)
with n1:
    canone = st.number_input("Canone (€/mese + IVA)", value=500)
with n2:
    anticipo = st.number_input("Anticipo (€)", value=0)
with n3:
    durata = st.selectbox("Durata (Mesi)", [24, 36, 48, 60], index=1)
with n4:
    km_anno = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("✨ GENERA PREVENTIVO BLACK"):
    try:
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255)
        
        # Header Info
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Consegna: {consegna}", ln=True, align="R")
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Spett.le {nome_cliente}", ln=True)
        pdf.ln(5)

        # Immagine Auto
        if foto_vettura:
            with open("temp_img.png", "wb") as f:
                f.write(foto_vettura.getbuffer())
            pdf.image("temp_img.png", 10, 65, 110)
            pdf.ln(70)
        else:
            pdf.ln(10)

        # Dati Veicolo
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{versione}", ln=True)
        pdf.ln(5)

        # Tabella Servizi e Penali
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 120, 255)
        pdf.cell(0, 10, "SERVIZI INCLUSI E PENALI:", ln=True)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 7, f"- RCA: Penale Euro {penale_rca}", ln=True)
        pdf.cell(0, 7, f"- Incendio e Furto: Penale {penale_if}", ln=True)
        pdf.cell(0, 7, f"- Protezione Danni (Kasko): Penale Euro {penale_kasko}", ln=True)
        pdf.cell(0, 7, "- Manutenzione Ordinaria e Straordinaria: INCLUSA", ln=True)
        pdf.cell(0, 7, "- Traino e Assistenza Stradale 24h: INCLUSA", ln=True)
        
        # Box Economico
        pdf.set_y(230)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 18, f" CANONE: EURO {canone},00 / mese + IVA ", ln=True, fill=True, align="C")
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 12)
        pdf.ln(2)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo} | Durata: {durata} mesi | Km totali: {km_anno*durata/12:,}".replace(",", "."), ln=True, align="C")

        # Consulente
        pdf.set_y(260)
        pdf.set_x(120)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, f"Consulente: {nome_cons}", ln=True)
        pdf.set_x(120)
        pdf.cell(0, 5, f"Email: {email_cons}", ln=True)

        pdf.output("web_preventivo.pdf")
        
        with open("web_preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA PREVENTIVO", f, "Preventivo_Maldarizzi.pdf", "application/pdf")
        st.balloons()

    except Exception as e:
        st.error(f"Errore: {e}")