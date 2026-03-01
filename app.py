import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF COMPLETAMENTE MODIFICATA ---
class MaldarizziPDF(FPDF):
    def header(self):
        # Fascia Nera Superiore molto più marcata (50mm invece di 40)
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 50, 'F')
        
        # Linea Argento Satinato (Sotto il logo)
        self.set_draw_color(192, 192, 192)
        self.set_line_width(0.8)
        self.line(0, 50, 210, 50)
        
        # Logo Maldarizzi - Grande e centrato
        if os.path.exists("logo.png"):
            # Centratura perfetta
            self.image("logo.png", 70, 12, 70)
        self.ln(55)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "maldarizzi.com | Offerta Premium Black Edition", 0, 0, "C")

# --- APP STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
st.title("🚗 Designer di Preventivi Maldarizzi")

# Sidebar per aggiornare il file Excel (Ripristinata)
st.sidebar.header("📁 Database")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open("dati.xlsx", "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Listino aggiornato!")

if not os.path.exists("dati.xlsx"):
    st.error("Manca il file dati.xlsx!")
    st.stop()

# Caricamento dati
excel = pd.ExcelFile("dati.xlsx")
foglio = st.sidebar.selectbox("Scegli Categoria", excel.sheet_names)
df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Info Consulente
st.sidebar.header("🤵 Consulente")
nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
tel_cons = st.sidebar.text_input("Tel/WhatsApp", "080 5322212")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")

# --- INTERFACCIA UTENTE ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Cliente")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.radio("Luogo di Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"], horizontal=True)
    note_libere = st.text_area("Note aggiuntive", placeholder="Accessori inclusi, colore, ecc...")

with col2:
    st.subheader("🚘 Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    foto_manuale = st.file_uploader("Cambia Foto Auto", type=["jpg", "png", "jpeg"])

st.markdown("---")
st.subheader("🛡️ Servizi e Penali")
s1, s2, s3 = st.columns(3)
with s1:
    p_rca = st.selectbox("Penale RCA (Euro)", ["0", "250"])
    p_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "5%", "10%"])
with s2:
    p_kasko = st.selectbox("Penale Danni (Euro)", ["0", "250", "500", "1000"])
    infort = st.checkbox("Infortunio Conducente", value=True)
with s3:
    g_tipo = st.radio("Pneumatici", ["ILLIMITATI", "A NUMERO"], horizontal=True)
    g_num = st.number_input("N. gomme", 4) if g_tipo == "A NUMERO" else "ILLIMITATI"

st.markdown("---")
st.subheader("💰 Offerta Finanziaria")
n1, n2, n3, n4 = st.columns(4)
with n1: canone = st.number_input("Canone (Euro)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
with n4: km = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("📝 GENERA PREVENTIVO"):
    pdf = MaldarizziPDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # Data a destra
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')} | CONSEGNA: {consegna}", ln=True, align="R")
    
    # Intestazione Spettabile
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"SPETT.LE {nome_cliente.upper()}", ln=True)
    pdf.ln(5)

    # Immagine Auto
    foto_path = None
    if foto_manuale:
        with open("tmp.png", "wb") as f: f.write(foto_manuale.getbuffer())
        foto_path = "tmp.png"
    else:
        for ext in [".jpg", ".png", ".jpeg", ".JPG"]:
            p = f"foto_vetture/{marca.upper()}{ext}"
            if os.path.exists(p): foto_path = p; break

    if foto_path:
        pdf.image(foto_path, 10, 80, 130)
        pdf.set_y(170)
    else:
        pdf.ln(10)

    # Dettagli Veicolo
    pdf.set_font("Arial", "B", 26)
    pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, versione)
    
    if note_libere:
        pdf.ln(4)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 5, f"Note e accessori: {note_libere}")

    # Blocchi Servizi
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "DETTAGLIO SERVIZI INCLUSI:", ln=True)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Arial", "", 11)
    servizi = [
        f"• Assicurazione RCA (Penale Euro {p_rca})",
        f"• Incendio e Furto (Penale {p_if})",
        f"• Copertura Danni/Kasko (Penale Euro {p_kasko})",
        f"• Manutenzione Totale (Ord/Straord)",
        f"• Pneumatici: {g_num}",
        f"• Assistenza Stradale H24"
    ]
    if infort: servizi.append("• Infortunio Conducente Incluso")
    
    y_serv = pdf.get_y()
    for i, s in enumerate(servizi):
        if i < 4:
            pdf.cell(90, 7, s, ln=True)
        else:
            if i == 4: pdf.set_xy(110, y_serv)
            pdf.set_x(110)
            pdf.cell(90, 7, s, ln=True)

    # Box Prezzo Black Edition (Ora lo rendiamo ancora più grande)
    pdf.set_y(235)
    pdf.set_fill_color(0, 0, 0)
    pdf.rect(10, 235, 190, 22, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 22, f"CANONE: EURO {canone},00 / MESE + IVA", ln=True, align="C")
    
    # Riepilogo Finanziario
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 13)
    pdf.ln(4)
    km_tot = int(km * durata / 12)
    pdf.cell(0, 8, f"Anticipo: Euro {anticipo}  |  Durata: {durata
