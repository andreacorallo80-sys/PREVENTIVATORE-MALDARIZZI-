import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF PROFESSIONALE PREMIUM BLACK ---
class MaldarizziPDF(FPDF):
    def header(self):
        # Sfondo Nero integrale per tutta la pagina
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 297, 'F')
        
        # Logo Maldarizzi in alto a sinistra
        if os.path.exists("logo.png"):
            self.image("logo.png", 12, 12, 55)
        
        # Linea sottile estetica Grigio Argento
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, 35, 200, 35)
        self.ln(38)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "maldarizzi.com | Offerta soggetta ad approvazione della società di noleggio", 0, 0, "C")

# --- CONFIGURAZIONE INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
st.title("🚀 Maldarizzi Rent - Designer di Preventivi")

NOME_FILE_FISSO = "dati.xlsx"

# Gestione Caricamento Listino
st.sidebar.header("📁 Gestione Database")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Database aggiornato!")

if not os.path.exists(NOME_FILE_FISSO):
    st.error("Carica il file dati.xlsx per iniziare!")
    st.stop()

# Caricamento Excel
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Scegli Categoria", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Dati Consulente
st.sidebar.header("🤵 Info Consulente")
nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")
tel_cons = st.sidebar.text_input("WhatsApp/Tel", "080 5322212")

# --- INTERFACCIA INPUT ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Cliente e Note")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.radio("Luogo di Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"], horizontal=True)
    note_libere = st.text_area("Note e Accessori (compariranno nel PDF)", placeholder="Es. Vernice Metallizzata, Pacchetto assistenza...")

with col2:
    st.subheader("🚘 Selezione Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    foto_manuale = st.file_uploader("Sostituisci foto auto", type=["jpg", "png", "jpeg"])

st.markdown("---")
st.subheader("🛡️ Servizi e Penali")
s1, s2, s3 = st.columns(3)
with s1:
    penale_rca = st.selectbox("Penale RCA (Euro)", ["0", "250"])
    penale_if = st.selectbox("Penale Incendio/Furto", ["0", "250", "500", "5%", "10%", "20%"])
with s2:
    penale_kasko = st.selectbox("Penale Kasko/Danni (Euro)", ["0", "250", "500", "1000", "2000"])
    infortunio = st.checkbox("Infortunio Conducente", value=True)
with s3:
    tipo_gomme = st.radio("Servizio Pneumatici", ["ILLIMITATI", "A NUMERO"], horizontal=True)
    num_gomme = st.number_input("Quantità gomme", value=4) if tipo_gomme == "A NUMERO" else "ILLIMITATI"

st.markdown("---")
st.subheader("💰 Parametri Noleggio")
n1, n2, n3, n4 = st.columns(4)
with n1: canone = st.number_input("Canone (Euro/mese + IVA)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Durata (Mesi)", [24, 36, 48, 60], index=1)
with n4: km_anno = st.number_input("Chilometri/Anno", value=15000)

# --- LOGICA GENERAZIONE PDF ---
if st.button("🌟 GENERA PREVENTIVO PREMIUM"):
    try:
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(255, 255, 255)
        
        # Data e Consegna (Allineato a Destra)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')} | CONSEGNA: {consegna}", ln=True, align="R")
        
        # Intestazione Spettabile
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"SPETT.LE {nome_cliente.upper()}", ln=True)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 5, "Di seguito l'offerta personalizzata Maldarizzi Rent per il noleggio della sua nuova vettura.")

        # Gestione Immagine
        foto_da_usare = None
        if foto_manuale:
            with open("temp_foto.png", "wb") as f: f.write(foto_manuale.getbuffer())
            foto_da_usare = "temp_foto.png"
        else:
            for ext in [".jpg", ".png", ".jpeg", ".JPG", ".PNG"]:
                path = f"foto_vetture/{marca.upper()}{ext}"
                if os.path.exists(path):
                    foto_da_usare = path
                    break

        if foto_da_usare:
            pdf.image(foto_da_usare, 10, 75, 115)
            pdf.set_y(150) # Sposta il testo sotto la foto
        else:
            pdf.ln(10)

        # Titolo Veicolo (Grande e Impattante)
        pdf.set_font("Arial", "B", 26)
        pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font("Arial", "", 13)
        pdf.set_text_color(200, 200, 200) # Grigio chiaro per versione
        pdf.multi_cell(0, 6, versione)
        
        # Note Libere
        if note_libere:
            pdf.ln(4)
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(160, 160, 160)
            pdf.multi_cell(0, 5, f"Dettagli aggiuntivi inclusi: {note_libere}")
            pdf.set_text_color(255, 255, 255)

        # Blocco Servizi (Disposti su 2 colonne per eleganza)
        pdf.ln(8)
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "SERVIZI INCLUSI E PENALI", ln=True)
        pdf.set_draw_color(100, 100, 100)
        pdf.line(10, pdf.get_y(), 100, pdf.get_y()) # Linea di separazione servizi
        pdf.ln(3)

        pdf.set_font("Arial", "", 10)
        servizi_txt = [
            f"• RCA: Penale Euro {penale_rca}",
            f"• Incendio e Furto: Penale {penale_if}",
            f"• Kasko (Danni): Penale Euro {penale_kasko}",
            f"• Pneumatici: {num_gomme}",
            "• Manutenzione Ordinaria/Straordinaria",
            "• Soccorso Stradale 24h"
        ]
        if infortunio: servizi_txt.append("• Infortunio Conducente")

        # Scrittura su due colonne
        y_start = pdf.get_y()
        for i, s in enumerate(servizi_txt):
            if i < 4:
                pdf.cell(90, 6, s, ln=True)
            else:
                if i == 4: pdf.set_xy(110, y_start)
                pdf.set_x(110)
                pdf.cell(90, 6, s, ln=True)

        # Box Prezzo (Massimo Contrasto)
        pdf.set_y(230)
        pdf.set_fill_color(255, 255, 255) # Sfondo Bianco
        pdf.set_text_color(0, 0, 0) # Testo Nero
        pdf.set_font("Arial", "B", 24)
        pdf.cell(0, 22, f" EURO {canone},00 / MESE + IVA ", ln=True, fill=True, align="C")
        
        # Dati Finanziari di Riepilogo
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 13)
        pdf.ln(3)
        km_tot = int(km_anno * durata / 12)
        pdf.cell(0, 8, f"Anticipo: Euro {anticipo}  |  Durata: {durata} Mesi  |  Km Totali: {km_tot:,}".replace(",", "."), ln=True, align="C")

        # Footer con Contatti Consulente
        pdf.set_y(265)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(0, 5, f"Consulente: {nome_cons}  |  Tel: {tel_cons}", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Email: {email_cons}", ln=True, align="C")

        # Output e Download
        pdf.output("preventivo.pdf")
        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA PREVENTIVO PRONTO", f, f"Offerta_{modello}.pdf")
        st.balloons()
            
    except Exception as e:
        st.error(f"Errore nella generazione del PDF: {e}")
