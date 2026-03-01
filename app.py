import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF MALDARIZZI BLACK EDITION ---
class MaldarizziPDF(FPDF):
    def header(self):
        # Sfondo Nero Integrale
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 297, 'F')
        
        # Logo Maldarizzi
        if os.path.exists("logo.png"):
            # Posizionato in alto a sinistra
            self.image("logo.png", 10, 12, 55)
        
        # Linea sottile Argento di separazione sotto il logo
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, 35, 200, 35)
        self.ln(38)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "maldarizzi.com | Offerta soggetta ad approvazione della società di noleggio", 0, 0, "C")

# --- APP STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Black Edition", layout="wide")
st.title("🖤 Maldarizzi Rent - Designer Preventivi")

NOME_FILE_FISSO = "dati.xlsx"

# Sidebar per caricamento listino
st.sidebar.header("⚙️ Pannello di Controllo")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Database aggiornato!")

if not os.path.exists(NOME_FILE_FISSO):
    st.info("Carica il file dati.xlsx per iniziare.")
    st.stop()

# Caricamento Excel
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Categoria Auto", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Dati Consulente
st.sidebar.markdown("---")
nome_cons = st.sidebar.text_input("Consulente", "CAMILLO VASIENTI")
tel_cons = st.sidebar.text_input("WhatsApp / Cell", "080 5322212")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")

# --- LAYOUT INPUT ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("👤 Cliente")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.selectbox("Modalità Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
    note = st.text_area("Note e Accessori (compariranno nel PDF)", placeholder="Es. Vernice Metallizzata, Cerchi in lega...")

with col2:
    st.subheader("🚘 Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Versione", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    foto_manuale = st.file_uploader("Carica Foto Personalizzata", type=["jpg", "png", "jpeg"])

st.markdown("---")
st.subheader("🛠️ Servizi e Penali")
s1, s2, s3 = st.columns(3)
with s1:
    p_rca = st.selectbox("Penale RCA (Euro)", ["0", "250"])
    p_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "5%", "10%"])
with s2:
    p_kasko = st.selectbox("Penale Danni (Euro)", ["0", "250", "500", "1000"])
    infort = st.checkbox("Infortunio Conducente", value=True)
with s3:
    g_tipo = st.radio("Pneumatici", ["ILLIMITATI", "A NUMERO"], horizontal=True)
    g_num = st.number_input("Quantità", 4) if g_tipo == "A NUMERO" else "ILLIMITATI"

st.markdown("---")
st.subheader("💰 Parametri Noleggio")
n1, n2, n3, n4 = st.columns(4)
with n1: canone = st.number_input("Canone Mensile (Euro)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
with n4: km = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("🚀 GENERA PREVENTIVO BLACK"):
    pdf = MaldarizziPDF()
    pdf.add_page()
    pdf.set_text_color(255, 255, 255)
    
    # Intestazione Data/Consegna
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')} | CONSEGNA: {consegna}", ln=True, align="R")
    
    # Destinatario
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"SPETT.LE {nome_cliente.upper()}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, "Di seguito l'offerta personalizzata Maldarizzi Rent per il noleggio della sua nuova vettura.")

    # Foto Auto
    foto_path = None
    if foto_manuale:
        with open("tmp.png", "wb") as f: f.write(foto_manuale.getbuffer())
        foto_path = "tmp.png"
    else:
        for ext in [".jpg", ".png", ".jpeg", ".JPG"]:
            p = f"foto_vetture/{marca.upper()}{ext}"
            if os.path.exists(p): foto_path = p; break

    if foto_path:
        pdf.image(foto_path, 10, 75, 115)
        pdf.set_y(150)
    else:
        pdf.ln(20)

    # Dettagli Veicolo (Bianco e Grande)
    pdf.set_font("Arial", "B", 26)
    pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
    
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(200, 200, 200)
    pdf.multi_cell(0, 6, versione)
    
    if note:
        pdf.ln(3)
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(160, 160, 160)
        pdf.multi_cell(0, 5, f"Dettagli inclusi: {note}")

    # Servizi (Stile Pulito)
    pdf.ln(8)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(255, 255, 255) # Bianco per risaltare sul nero
    pdf.cell(0, 8, "SERVIZI INCLUSI E PENALI", ln=True)
    
    # Linea di separazione servizi
    pdf.set_draw_color(100, 100, 100)
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Arial", "", 10)
    servizi_txt = [
        f"• RCA: Penale Euro {p_rca}",
        f"• Incendio e Furto: Penale {p_if}",
        f"• Kasko (Danni): Penale Euro {p_kasko}",
        f"• Manutenzione Ordinaria/Straord.",
        f"• Pneumatici: {g_num}",
        f"• Soccorso Stradale H24",
    ]
    if infort: servizi_txt.append("• Infortunio Conducente: INCLUSO")
    
    # Scrittura su due colonne
    curr_y = pdf.get_y()
    for i, s in enumerate(servizi_txt):
        if i < 4:
            pdf.cell(90, 6, s, ln=True)
        else:
            if i == 4: pdf.set_xy(110, curr_y)
            pdf.set_x(110)
            pdf.cell(90, 6, s, ln=True)

    # Box Prezzo Bianco (Contrasto Massimo)
    pdf.set_y(230)
    pdf.set_fill_color(255, 255, 255) # Bianco
    pdf.set_text_color(0, 0, 0) # Testo Nero
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 22, f" EURO {canone},00 / MESE + IVA ", ln=True, fill=True, align="C")
    
    # Dettagli Finanziari Sotto il Box
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.ln(3)
    km_tot = int(km * durata / 12)
    pdf.cell(0, 8, f"Anticipo: Euro {anticipo}  |  Durata: {durata} Mesi  |  Km Totali: {km_tot:,}".replace(",", "."), ln=True, align="C")

    # Consulente in Grigio Argento
    pdf.set_y(265)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 5, f"Consulente: {nome_cons}  |  Email: {email_cons}", ln=True, align="C")
    pdf.cell(0, 5, f"WhatsApp/Tel: {tel_cons}", ln=True, align="C")

    pdf.output("preventivo_maldarizzi.pdf")
    with open("preventivo_maldarizzi.pdf", "rb") as f:
        st.download_button("📩 SCARICA PREVENTIVO", f, f"Preventivo_{modello}.pdf")
