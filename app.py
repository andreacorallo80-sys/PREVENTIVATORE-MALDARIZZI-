import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime

# --- CLASSE PDF MODERNA: FASCIA NERA + CORPO BIANCO ---
class MaldarizziPDF(FPDF):
    def header(self):
        # Fascia Nera Superiore
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 40, 'F')
        
        # Linea sottile estetica Grigio Argento sotto la fascia
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(0, 40, 210, 40)
        
        # Logo Maldarizzi al Centro della fascia
        if os.path.exists("logo.png"):
            # Centriamo il logo: (210mm - 60mm) / 2 = 75mm
            self.image("logo.png", 75, 10, 60)
        self.ln(45)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "maldarizzi.com | Offerta soggetta ad approvazione", 0, 0, "C")

# --- APP STREAMLIT ---
st.set_page_config(page_title="Maldarizzi Rent Pro", layout="wide")
st.title("🚗 Designer di Preventivi Maldarizzi")

NOME_FILE_FISSO = "dati.xlsx"

# Sidebar Gestione
st.sidebar.header("📁 Database")
uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
if uploaded_excel:
    with open(NOME_FILE_FISSO, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    st.sidebar.success("Dati aggiornati!")

if not os.path.exists(NOME_FILE_FISSO):
    st.error("Manca il file dati.xlsx!")
    st.stop()

# Caricamento Dati
excel = pd.ExcelFile(NOME_FILE_FISSO)
foglio = st.sidebar.selectbox("Categoria", excel.sheet_names)
df = pd.read_excel(NOME_FILE_FISSO, sheet_name=foglio, dtype=str)
df.columns = df.columns.str.strip()

# Info Consulente
st.sidebar.header("🤵 Consulente")
nome_cons = st.sidebar.text_input("Nome", "CAMILLO VASIENTI")
tel_cons = st.sidebar.text_input("WhatsApp (es. 39347...)", "080 5322212")
email_cons = st.sidebar.text_input("Email", "c.vasienti@maldarizzi.com")

# --- INTERFACCIA UTENTE ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Cliente")
    nome_cliente = st.text_input("Nome Cliente", "Gentile Cliente")
    consegna = st.radio("Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"], horizontal=True)
    note_libere = st.text_area("Note aggiuntive", placeholder="Accessori, colore, pacchetti inclusi...")

with col2:
    st.subheader("🚘 Veicolo")
    marca = st.selectbox("Marca", sorted(df['Brand Description'].unique()))
    modello = st.selectbox("Modello", sorted(df[df['Brand Description']==marca]['Vehicle Set description'].unique()))
    versione = st.selectbox("Allestimento", sorted(df[(df['Brand Description']==marca) & (df['Vehicle Set description']==modello)]['Jato Product Description'].unique()))
    foto_manuale = st.file_uploader("Cambia Foto Auto", type=["jpg", "png", "jpeg"])

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
st.subheader("💰 Offerta")
n1, n2, n3, n4 = st.columns(4)
with n1: canone = st.number_input("Canone (Euro)", value=500)
with n2: anticipo = st.number_input("Anticipo (Euro)", value=0)
with n3: durata = st.selectbox("Mesi", [24, 36, 48, 60], index=1)
with n4: km = st.number_input("Km/Anno", value=15000)

# --- GENERAZIONE PDF ---
if st.button("✨ GENERA E FAI PIOVERE AUTO"):
    pdf = MaldarizziPDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # Data e Luogo
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 10, f"DATA: {datetime.now().strftime('%d/%m/%Y')} | CONSEGNA: {consegna}", ln=True, align="R")
    
    # Destinatario
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
        pdf.image(foto_path, 10, 75, 120)
        pdf.set_y(155)
    else:
        pdf.ln(10)

    # Dettagli Auto
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 15, f"{marca} {modello}".upper(), ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 6, versione)
    
    if note_libere:
        pdf.ln(2)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 5, f"Note: {note_libere}")

    # Servizi
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "SERVIZI INCLUSI NELL'OFFERTA:", ln=True)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Arial", "", 11)
    servizi = [
        f"• Assicurazione RCA (Penale Euro {p_rca})",
        f"• Incendio e Furto (Penale {p_if})",
        f"• Copertura Danni/Kasko (Penale Euro {p_kasko})",
        f"• Manutenzione Ordinaria e Straordinaria Inclusa",
        f"• Gestione Pneumatici: {g_num}",
        f"• Soccorso Stradale e Traino H24"
    ]
    if infort: servizi.append("• Assicurazione Infortunio Conducente")
    
    y_serv = pdf.get_y()
    for i, s in enumerate(servizi):
        if i < 4:
            pdf.cell(90, 7, s, ln=True)
        else:
            if i == 4: pdf.set_xy(110, y_serv)
            pdf.set_x(110)
            pdf.cell(90, 7, s, ln=True)

    # Box Economico
    pdf.set_y(230)
    pdf.set_fill_color(0, 0, 0)
    pdf.rect(10, 230, 190, 25, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 25, f"CANONE: EURO {canone},00 / MESE + IVA", ln=True, align="C")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.ln(2)
    km_tot = int(km * durata / 12)
    pdf.cell(0, 8, f"Anticipo: Euro {anticipo}  |  Durata: {durata} Mesi  |  Km Totali: {km_tot:,}".replace(",", "."), ln=True, align="C")

    # Footer Consulente
    pdf.set_y(265)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, f"Consulente: {nome_cons} | Tel: {tel_cons}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"E-mail: {email_cons}", ln=True, align="C")

    pdf.output("preventivo.pdf")

    # --- EFFETTO PIOGGIA DI MACCHINE ---
    st.markdown(
        """
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
            <style>
                @keyframes fall {
                    0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
                    100% { transform: translateY(110vh) rotate(360deg); opacity: 0; }
                }
                .car {
                    position: absolute;
                    font-size: 40px;
                    animation: fall linear forwards;
                }
            </style>
            """ + "".join([
                f'<div class="car" style="left: {i*7}%; animation-duration: {1.5 + (i%2)}s; animation-delay: {i*0.1}s;">{"🚗" if i%2==0 else "🚙"}</div>'
                for i in range(15)
            ]) + """
        </div>
        """,
        unsafe_allow_html=True
    )

    with open("preventivo.pdf", "rb") as f:
        st.download_button("📩 SCARICA IL TUO PREVENTIVO", f, f"Offerta_{modello}.pdf")
