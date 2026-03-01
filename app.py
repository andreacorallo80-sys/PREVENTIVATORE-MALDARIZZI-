import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF PREMIUM: FASCIA NERA + LOGO CENTRATO ---
class MaldarizziPDF(FPDF):
    def header(self):
        # Fascia Nera Superiore Alta
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 45, 'F')
        
        # Linea Argento di Separazione Sotto la Fascia
        self.set_draw_color(192, 192, 192)
        self.set_line_width(0.8)
        self.line(0, 45, 210, 45)
        
        # Logo Maldarizzi - CENTRATO
        if os.path.exists("logo.png"):
            self.image("logo.png", 70, 10, 70)
        self.ln(50)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, "maldarizzi.com | Offerta Premium Maldarizzi Rent", 0, 0, "C")

# --- APP INTERFACCIA ---
st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
st.title("🚗🚀 NUOVO PORTALE MALDARIZZI 2026")

NOME_FILE_FISSO = "dati.xlsx"

# Sidebar Gestione
st.sidebar.header("📁 Gestione Database")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Database aggiornato!")

if not os.path.exists(NOME_FILE_FISSO):
    st.error("File dati.xlsx non trovato!")
    st.stop()

# Caricamento Dati
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Seleziona Categoria", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Info Consulente
st.sidebar.header("🤵 Consulente")
nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")

# --- INTERFACCIA INPUT ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Cliente")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.radio("Luogo di Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"], horizontal=True)
    note_libere = st.text_area("Note aggiuntive", height=100)

with col2:
    st.subheader("🚘 Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    foto_manuale = st.file_uploader("Carica foto auto", type=["jpg", "png", "jpeg"])

st.markdown("---")
st.subheader("🛡️ Servizi")
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
with n1: canone = st.number_input("Canone Mensile (Euro)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Durata (Mesi)", [24, 36, 48, 60], index=1)
with n4: km = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("📝 CREA PREVENTIVO PREMIUM"):
    try:
        pdf = MaldarizziPDF()
        pdf.add_page()
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')} | CONSEGNA: {consegna}", ln=True, align="R")
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"SPETT.LE {nome_cliente.upper()}", ln=True)
        pdf.ln(5)

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
            pdf.image(foto_path, 10, 80, 125)
            pdf.set_y(175)
        else:
            pdf.ln(15)

        # Testi Auto
        pdf.set_font("Arial", "B", 26)
        pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
        pdf.set_font("Arial", "", 13)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 6, versione)
        
        if note_libere:
            pdf.ln(5)
            pdf.set_font("Arial", "I", 10)
            pdf.multi_cell(0, 5, f"Allestimento e note: {note_libere}")

        # Servizi (PULIZIA SIMBOLI EURO)
        pdf.ln(10)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "DETTAGLIO SERVIZI INCLUSI:", ln=True)
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 60, pdf.get_y())
        pdf.ln(5)

        pdf.set_font("Arial", "", 11)
        # Qui usiamo solo la parola 'Euro' per evitare il crash
        servizi = [
            f"- RCA: Penale Euro {p_rca}",
            f"- Incendio e Furto: Penale {p_if}",
            f"- Kasko (Danni): Penale Euro {p_kasko}",
            f"- Pneumatici: {g_num}",
            "- Manutenzione Totale (Ord/Straord)",
            "- Assistenza Stradale H24"
        ]
        if infort: servizi.append("- Infortunio Conducente Incluso")
        
        y_serv = pdf.get_y()
        for i, s in enumerate(servizi):
            # Usiamo encode('latin-1', 'replace').decode('latin-1') per sicurezza
            s_clean = s.encode('latin-1', 'replace').decode('latin-1')
            if i < 4:
                pdf.cell(90, 7, s_clean, ln=True)
            else:
                if i == 4: pdf.set_xy(110, y_serv)
                pdf.set_x(110)
                pdf.cell(90, 7, s_clean, ln=True)

        # Box Prezzo Black
        pdf.set_y(235)
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(10, 235, 190, 25, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 22)
        pdf.cell(0, 25, f"CANONE: EURO {canone},00 / MESE + IVA", ln=True, align="C")
        
        # Riepilogo Finanziario
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 13)
        pdf.ln(4)
        km_tot = int(km * durata / 12)
        riepilogo = f"Anticipo: Euro {anticipo}  |  Durata: {durata} Mesi  |  Km Totali: {km_tot:,}".replace(",", ".")
        pdf.cell(0, 8, riepilogo.encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")

        # Footer Consulente
        pdf.set_y(270)
        pdf.set_font("Arial", "B", 10)
        footer_cons = f"{nome_cons} | Tel: {tel_cons}".encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 5, footer_cons, ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, email_cons, ln=True, align="C")

        pdf.output("preventivo.pdf")

        # --- PIOGGIA DI AUTO ---
        st.markdown("""
            <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
                <style>
                    @keyframes fall {
                        0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
                        100% { transform: translateY(110vh) rotate(360deg); opacity: 0; }
                    }
                    .car { position: absolute; font-size: 40px; animation: fall linear forwards; }
                </style>
                """ + "".join([f'<div class="car" style="left: {i*8}%; animation-duration: {1.5+(i%2)}s; animation-delay: {i*0.1}s;">🚗</div>' for i in range(12)]) + """
            </div>""", unsafe_allow_html=True)

        with open("preventivo.pdf", "rb") as f:
            st.download_button("📩 SCARICA IL PREVENTIVO", f, f"Offerta_{modello}.pdf")

    except Exception as e:
        st.error(f"Errore tecnico durante la stampa: {e}")
