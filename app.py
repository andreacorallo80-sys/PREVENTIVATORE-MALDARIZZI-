import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF PROFESSIONALE ---
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
        self.cell(0, 10, "https://noleggio.maldarizzi.com/ - Offerta soggetta ad approvazione", 0, 0, "C")

# --- APP STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
st.title("🚀 Maldarizzi Rent - Preventivatore Business")

NOME_FILE_FISSO = "dati.xlsx"

# Gestione Caricamento Listino
st.sidebar.header("📁 Gestione Dati")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Listino aggiornato!")

if not os.path.exists(NOME_FILE_FISSO):
    st.error("Manca il file dati.xlsx!")
    st.stop()

# Caricamento Excel
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Dati Consulente
st.sidebar.header("🤵 Info Consulente")
nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
tel_cons = st.sidebar.text_input("Cellulare / WhatsApp", "080 5322212")

# --- INTERFACCIA ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Cliente e Note")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.radio("Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"], horizontal=True)
    note_libere = st.text_area("Note Aggiuntive", placeholder="Accessori o promozioni...")

with col2:
    st.subheader("🚘 Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    
    # Cerca foto automatica (prova diverse estensioni)
    foto_manuale = st.file_uploader("Sostituisci foto (opzionale)", type=["jpg", "png", "jpeg"])

st.markdown("---")
st.subheader("🛡️ Servizi e Penali")
s1, s2, s3 = st.columns(3)
with s1:
    penale_rca = st.selectbox("Penale RCA (Euro)", ["0", "250"])
    penale_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "0%", "5%", "10%", "20%"])
with s2:
    penale_kasko = st.selectbox("Penale Kasko (Euro)", ["0", "250", "500", "1000", "2000"])
    infortunio = st.checkbox("Infortunio Conducente", value=True)
with s3:
    tipo_gomme = st.radio("Pneumatici", ["ILLIMITATI", "A NUMERO"], horizontal=True)
    num_gomme = st.number_input("Quantità gomme", value=4) if tipo_gomme == "A NUMERO" else "ILLIMITATI"

st.markdown("---")
st.subheader("💰 Economia")
n1, n2, n3, n4 = st.columns(4)
with n1: canone = st.number_input("Canone (Euro + IVA)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Durata (Mesi)", [24, 36, 48, 60], index=1)
with n4: km_anno = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("🚀 GENERA PREVENTIVO"):
    try:
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255)
        
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Data: {datetime.now().strftime('%d/%m/%Y')} | Consegna: {consegna}", ln=True, align="R")
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Spett.le {nome_cliente}", ln=True)

        # Gestione Foto
        foto_da_usare = None
        if foto_manuale:
            with open("temp_foto.png", "wb") as f: f.write(foto_manuale.getbuffer())
            foto_da_usare = "temp_foto.png"
        else:
            # Prova a cercare il brand con varie estensioni
            for ext in [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]:
                path = f"foto_vetture/{marca.upper()}{ext}"
                if os.path.exists(path):
                    foto_da_usare = path
                    break

        if foto_da_usare:
            pdf.image(foto_da_usare, 10, 60, 100)
            pdf.ln(65)
        else:
            pdf.ln(10)

        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, f"{versione}")
        
        if note_libere:
            pdf.ln(5)
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(200, 200, 200)
            pdf.multi_cell(0, 5, f"Note: {note_libere}")
            pdf.set_text_color(255, 255, 255)

        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 120, 255)
        pdf.cell(0, 10, "SERVIZI INCLUSI E PENALI:", ln=True)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "", 10)
        
        servizi = [
            f"- RCA: Penale Euro {penale_rca}",
            f"- Incendio e Furto: Penale {penale_if}",
            f"- Kasko (Danni): Penale Euro {penale_kasko}",
            f"- Pneumatici: {num_gomme}",
            "- Manutenzione Ordinaria/Straordinaria: INCLUSA",
            "- Soccorso Stradale 24h: INCLUSO"
        ]
        if infortunio: servizi.append("- Infortunio Conducente: INCLUSO")
        for s in servizi: pdf.cell(0, 6, s, ln=True)

        # Box Prezzo (Sostituito € con Euro)
        pdf.set_y(230)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 18, f" CANONE: EURO {canone},00 / mese + IVA ", ln=True, fill=True, align="C")
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 12)
        pdf.ln(2)
        # Calcolo km totali e rimosso simbolo €
        km_tot = int(km_anno * durata / 12)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo} | Durata: {durata} mesi | Km totali: {km_tot:,}".replace(",", "."), ln=True, align="C")

        pdf.set_y(260)
        pdf.set_x(120)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, f"Consulente: {nome_cons}", ln=True)
        pdf.set_x(120)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Email: {email_cons}", ln=True)
        pdf.set_x(120)
        pdf.cell(0, 5, f"WhatsApp/Tel: {tel_cons}", ln=True)

        pdf.output("preventivo.pdf")
        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf")
            
    except Exception as e:
        st.error(f"Errore nella generazione del PDF: {e}")
