import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF PREMIUM EDITION ---
class MaldarizziPDF(FPDF):
    def header(self):
        # Sfondo Nero Totale
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 297, 'F')
        
        # Logo Maldarizzi
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 12, 50)
        
        # Linea di accento Blu Maldarizzi (in alto)
        self.set_draw_color(0, 51, 153)
        self.set_line_width(1.5)
        self.line(10, 32, 200, 32)
        self.ln(35)

    def footer(self):
        self.set_y(-20)
        self.set_font("Arial", "I", 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "maldarizzi.com | Documentazione ad uso commerciale", 0, 0, "C")

# --- APP STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Pro", layout="wide")
st.title("🚗 Maldarizzi Rent - Designer di Preventivi")

NOME_FILE_FISSO = "dati.xlsx"

# Sidebar per caricamento listino
st.sidebar.header("⚙️ Impostazioni")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Listino caricato!")

if not os.path.exists(NOME_FILE_FISSO):
    st.info("Carica il file dati.xlsx per iniziare.")
    st.stop()

# Caricamento Excel
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Dati Consulente
st.sidebar.markdown("---")
nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

# --- LAYOUT INPUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👤 Cliente")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.selectbox("Luogo di Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
    note = st.text_area("Note e Accessori", placeholder="Es. Cerchi in lega 19'', Vernice Metallizzata...")

with col2:
    st.subheader("🚘 Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Versione", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    foto_manuale = st.file_uploader("Cambia Foto Auto", type=["jpg", "png", "jpeg"])

st.markdown("---")
st.subheader("🛠️ Configurazione Servizi")
s1, s2, s3 = st.columns(3)
with s1:
    p_rca = st.selectbox("Penale RCA (Euro)", ["0", "250"])
    p_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "5%", "10%"])
with s2:
    p_kasko = st.selectbox("Penale Danni (Euro)", ["0", "250", "500", "1000"])
    infort = st.checkbox("Infortunio Conducente", value=True)
with s3:
    g_tipo = st.radio("Pneumatici", ["ILLIMITATI", "A NUMERO"])
    g_num = st.number_input("Quantità", 4) if g_tipo == "A NUMERO" else "ILLIMITATI"

st.markdown("---")
st.subheader("💳 Offerta Finanziaria")
n1, n2, n3, n4 = st.columns(4)
with n1: canone = st.number_input("Canone Mensile (Euro)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
with n4: km = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("🌟 GENERA PREVENTIVO PREMIUM"):
    pdf = MaldarizziPDF()
    pdf.add_page()
    pdf.set_text_color(255, 255, 255)
    
    # Intestazione Data/Consegna
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')} | CONSEGNA: {consegna}", ln=True, align="R")
    
    # Benvenuto
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"SPETT.LE {nome_cliente.upper()}", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 5, "Abbiamo il piacere di presentarle l'offerta di noleggio a lungo termine Maldarizzi Rent studiata per lei.")

    # Foto Auto Grande
    foto_path = None
    if foto_manuale:
        with open("tmp.png", "wb") as f: f.write(foto_manuale.getbuffer())
        foto_path = "tmp.png"
    else:
        for ext in [".jpg", ".png", ".jpeg"]:
            p = f"foto_vetture/{marca.upper()}{ext}"
            if os.path.exists(p): foto_path = p; break

    if foto_path:
        pdf.image(foto_path, 10, 75, 120)
        pdf.set_y(145)
    else:
        pdf.ln(20)

    # Titolo Auto
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
    
    pdf.set_font("Arial", "", 13)
    pdf.set_text_color(200, 200, 200)
    pdf.multi_cell(0, 6, versione)
    
    # Note
    if note:
        pdf.ln(2)
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(150, 150, 150)
        pdf.multi_cell(0, 5, f"Allestimento incluso: {note}")

    # Blocchi Servizi
    pdf.ln(8)
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(0, 120, 255) # Blu Maldarizzi Light
    pdf.cell(0, 10, "DETTAGLIO SERVIZI INCLUSI:", ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(255, 255, 255)
    
    servizi_col1 = [
        f"• RCA: Penale Euro {p_rca}",
        f"• Incendio e Furto: Penale {p_if}",
        f"• Kasko (Danni): Penale Euro {p_kasko}",
        f"• Pneumatici: {g_num}"
    ]
    servizi_col2 = [
        "• Manutenzione Ordinaria/Straord.",
        "• Soccorso Stradale H24",
        f"• Infortunio Conducente: {'SI' if infort else 'NO'}"
    ]
    
    # Scrittura su due colonne per eleganza
    y_servizi = pdf.get_y()
    for s in servizi_col1: pdf.cell(90, 6, s, ln=True)
    pdf.set_xy(110, y_servizi)
    for s in servizi_col2: pdf.cell(90, 6, s, ln=True)

    # Area Economica (Pezzo Forte)
    pdf.set_y(230)
    pdf.set_fill_color(255, 255, 255) # Box Bianco
    pdf.set_text_color(0, 0, 0) # Testo Nero
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 22, f" EURO {canone},00 / MESE + IVA ", ln=True, fill=True, align="C")
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 13)
    pdf.ln(3)
    km_tot = int(km * durata / 12)
    pdf.cell(0, 8, f"Anticipo: Euro {anticipo}  |  Durata: {durata} Mesi  |  Km Totali: {km_tot:,}".replace(",", "."), ln=True, align="C")

    # Consulente
    pdf.set_y(265)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(0, 120, 255)
    pdf.cell(0, 5, f"Consulente: {nome_cons}  |  Tel/WhatsApp: {tel_cons}", ln=True, align="C")

    pdf.output("preventivo_maldarizzi.pdf")
    with open("preventivo_maldarizzi.pdf", "rb") as f:
        st.download_button("📩 SCARICA IL TUO CAPOLAVORO", f, f"Offerta_{modello}.pdf")
    st.balloons()
