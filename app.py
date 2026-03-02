import streamlit as st
import pandas as pd
import os
import re
import PyPDF2
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

# --- INIZIALIZZAZIONE VARIABILI IN MEMORIA ---
if "lista_preventivi" not in st.session_state: st.session_state["lista_preventivi"] = []
if "val_canone" not in st.session_state: st.session_state["val_canone"] = 500.0
if "val_durata" not in st.session_state: st.session_state["val_durata"] = 36
if "val_km" not in st.session_state: st.session_state["val_km"] = 15000
if "val_anticipo" not in st.session_state: st.session_state["val_anticipo"] = 0.0
if "val_cliente" not in st.session_state: st.session_state["val_cliente"] = "Gentile CLIENTE"
if "val_input_mode" not in st.session_state: st.session_state["val_input_mode"] = "Da Listino" # NUOVA LOGICA
if "val_marca_stampa" not in st.session_state: st.session_state["val_marca_stampa"] = ""
if "val_versione_stampa" not in st.session_state: st.session_state["val_versione_stampa"] = ""
if "val_p_rca" not in st.session_state: st.session_state["val_p_rca"] = "250 Euro"
if "val_p_if" not in st.session_state: st.session_state["val_p_if"] = "10%"
if "val_p_kasko" not in st.session_state: st.session_state["val_p_kasko"] = "500 Euro"

if check_password():
    # --- 2. CLASSE PDF "MALDARIZZI MULTI-PAGE" ---
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
            if os.path.exists("slider-maldarizzirent.jpg"):
                self.image("slider-maldarizzirent.jpg", 0, 0, 210, 297)
            else:
                self.set_fill_color(30, 30, 30)
                self.rect(0, 0, 210, 297, 'F')

            self.set_fill_color(0, 0, 0)
            self.rect(0, 0, 210, 40, 'F')
            if os.path.exists("logo.png"):
                self.image("logo.png", 75, 8, 60)
            
            self.set_y(45)
            self.set_font(self.f_f, "B", 20)
            self.set_text_color(255, 255, 255)
            self.cell(0, 10, "IL TUO PREVENTIVO", align="C", ln=True)

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Copilota", layout="wide")
    try: locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
    except: pass

    # --- SIDEBAR: LETTURA SMART PDF ---
    st.sidebar.header("📥 Importa PDF Portale")
    pdf_portale = st.sidebar.file_uploader("Carica PDF (Arval, Leasys, Ayvens)", type=["pdf"])
    
    if pdf_portale and st.sidebar.button("🧠 Analizza e Compila Dati"):
        try:
            reader = PyPDF2.PdfReader(pdf_portale)
            testo_estratto = ""
            for page in reader.pages:
                testo_estratto += page.extract_text() + " \n "
            
            testo_pulito = testo_estratto.replace('\r', ' ')
            
            # 1. DURATA
            m_dur = re.search(r'(24|36|48|60)\s*mesi', testo_pulito, re.IGNORECASE)
            if m_dur: 
                st.session_state["val_durata"] = int(m_dur.group(1))

            # 2. KM TOTALI O ANNUI
            m_km = re.search(r'(?:km totali|percorrenza|km totall)[\s\S]{0,30}?(\d{2,3}[\s\.]?\d{3})', testo_pulito, re.IGNORECASE)
            if not m_km: m_km = re.search(r'(\d{2,3}[\s\.]?\d{3})\s*km', testo_pulito, re.IGNORECASE)
            
            if m_km:
                km_tot = int(re.sub(r'\D', '', m_km.group(1)))
                if km_tot > 30000:
                    mesi = st.session_state.get("val_durata", 36)
                    st.session_state["val_km"] = int((km_tot / mesi) * 12)
                else:
                    st.session_state["val_km"] = km_tot

            # 3. CANONE
            m_canoni = re.findall(r'(\d{2,4}[.,]\d{2})', testo_pulito)
            valid_canoni = []
            for c in m_canoni:
                val = float(c.replace('.', '').replace(',', '.'))
                if 150 < val < 4000: valid_canoni.append(val)
            if valid_canoni:
                st.session_state["val_canone"] = max(valid_canoni)

            # 4. CLIENTI, VEICOLI E PENALI
            testo_upper = testo_pulito.upper()
            
            # Innesco la modalità TESTO LIBERO (così non usiamo il listino), ma non tocco "Nuovo/Usato"
            st.session_state["val_input_mode"] = "Testo Libero"
            
            if "ARVAL" in testo_upper:
                m_cli = re.search(r'Ragione Sociale[\s\S]{0,10}?([A-Z\s]{5,})', testo_pulito)
                if m_cli: st.session_state["val_cliente"] = m_cli.group(1).strip()
                m_vei = re.search(r'proposta di noleggio per il veicolo\s*([^\n]+)', testo_pulito, re.IGNORECASE)
                if m_vei: 
                    vei_str = m_vei.group(1).strip()
                    st.session_state["val_marca_stampa"] = vei_str.split()[0]
                    st.session_state["val_versione_stampa"] = vei_str
                    
            elif "LEASYS" in testo_upper:
                m_cli = re.search(r'CONSULENTE DI VENDITA[\s\S]*?\n\n([^\n]+)', testo_pulito)
                if m_cli: st.session_state["val_cliente"] = m_cli.group(1).strip()
                m_vei = re.search(r'km totall?[\s\S]*?\n\n([^\n]+)\n([^\n]+)\n\n([^\n]+)', testo_pulito, re.IGNORECASE)
                if m_vei:
                    st.session_state["val_marca_stampa"] = m_vei.group(1).strip()
                    st.session_state["val_versione_stampa"] = m_vei.group(3).strip()
                    
            elif "AYVENS" in testo_upper or "ALD " in testo_upper:
                m_cli = re.search(r'Att\.ne di\s*:\s*([^\n]+)', testo_pulito, re.IGNORECASE)
                if m_cli: st.session_state["val_cliente"] = m_cli.group(1).strip()
                m_vei = re.search(r'Veicolo\s*:\s*([^\n]+\n?[^\n]+)', testo_pulito, re.IGNORECASE)
                if m_vei:
                    vei_str = m_vei.group(1).replace('\n', ' ').strip()
                    st.session_state["val_marca_stampa"] = vei_str.split()[0]
                    st.session_state["val_versione_stampa"] = vei_str

            # CHECK PENALI BASE
            if "500" in testo_pulito and ("Danni" in testo_pulito or "Kasko" in testo_pulito): st.session_state["val_p_kasko"] = "500 Euro"
            elif "1000" in testo_pulito: st.session_state["val_p_kasko"] = "1000 Euro"
            if "250" in testo_pulito and "RCA" in testo_pulito: st.session_state["val_p_rca"] = "250 Euro"
            elif "500" in testo_pulito and "RCA" in testo_pulito: st.session_state["val_p_rca"] = "500 Euro"
            if "10%" in testo_pulito: st.session_state["val_p_if"] = "10%"
            elif "5%" in testo_pulito: st.session_state["val_p_if"] = "5%"

            st.sidebar.success("✅ Dati importati in modalità Testo Libero!")
            st.rerun()
            
        except Exception as e:
            st.sidebar.error("Errore nella lettura del PDF. Riprova.")

    st.sidebar.markdown("---")
    st.sidebar.header("📁 Database Listino")
    uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
    if uploaded_excel:
        with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
        st.sidebar.success("Database aggiornato!")

    if os.path.exists("dati.xlsx"):
        excel = pd.ExcelFile("dati.xlsx")
        foglio = st.sidebar.selectbox("Seleziona Categoria", excel.sheet_names)
        df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
    else:
        st.error("Carica dati.xlsx per procedere")
        st.stop()
    
    st.sidebar.markdown("---")
    g_validita = st.sidebar.slider("Validità Offerta (gg)", 1, 30, 30)
    nome_cons = st.sidebar.text_input("Consulente", "GRAZIA DEL VECCHIO")
    email_cons = st.sidebar.text_input("Email", "g.delvecchio@maldarizzi.com")
    tel_cons = st.sidebar.text_input("WhatsApp", "080 5322212")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("👤 Cliente")
        nome_cliente = st.text_input("Nome Cliente", value=st.session_state.get("val_cliente", ""))
        consegna = st.selectbox("Luogo Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
        
        # Stato Veicolo serve SOLO per la stampa
        t_veicolo = st.radio("Stato Veicolo (Stampa)", ["Nuovo", "Usato"], horizontal=True)
        note_p = st.text_area("Note e optional", height=70)
    
    with c2:
        st.subheader("🚘 Veicolo")
        
        # NUOVO TOGGLE: Scegli se usare il listino o scrivere a mano
        idx_input_mode = 1 if st.session_state.get("val_input_mode") == "Testo Libero" else 0
        input_mode = st.radio("Modalità Inserimento", ["Da Listino", "Testo Libero"], horizontal=True, index=idx_input_mode)
        
        if input_mode == "Testo Libero":
            marca_stampa = st.text_input("Marca", value=st.session_state.get("val_marca_stampa", ""))
            versione_stampa = st.text_area("Allestimento/Versione", value=st.session_state.get("val_versione_stampa", ""))
        else:
            marca_sel = st.selectbox("Marca", sorted(df['Brand Description'].unique().tolist()))
            modello_sel = st.selectbox("Modello (Filtro)", sorted(df[df['Brand Description']==marca_sel]['Vehicle Set description'].unique().tolist()))
            versione_sel = st.selectbox("Versione/Allestimento", sorted(df[(df['Brand Description']==marca_sel) & (df['Vehicle Set description']==modello_sel)]['Jato Product Description'].unique().tolist()))
            marca_stampa = marca_sel
            versione_stampa = versione_sel
        
        foto_m = st.file_uploader("Foto Auto (Opzionale)", type=["jpg", "png", "jpeg"])

    st.markdown("---")
    st.subheader("🛡️ Servizi e Penali")
    s1, s2, s3 = st.columns(3)
    
    with s1:
        rca_options = ["0 Euro", "250 Euro", "500 Euro"]
        rca_idx = rca_options.index(st.session_state.get("val_p_rca", "250 Euro")) if st.session_state.get("val_p_rca", "250 Euro") in rca_options else 1
        p_rca = st.selectbox("Penale RCA", rca_options, index=rca_idx)
        
        if_options = ["0%", "5%", "10%", "250 Euro"]
        if_idx = if_options.index(st.session_state.get("val_p_if", "10%")) if st.session_state.get("val_p_if", "10%") in if_options else 2
        p_if = st.selectbox("Penale Incendio/Furto", if_options, index=if_idx)
    
    with s2:
        kasko_options = ["0 Euro", "250 Euro", "500 Euro", "1000 Euro"]
        kasko_idx = kasko_options.index(st.session_state.get("val_p_kasko", "500 Euro")) if st.session_state.get("val_p_kasko", "500 Euro") in kasko_options else 2
        p_kasko = st.selectbox("Penale Danni/Kasko", kasko_options, index=kasko_idx)
        infort = st.checkbox("Infortunio Conducente (PAI)", value=True)
    
    with s3:
        usa_gomme = st.checkbox("Includere Pneumatici?", value=True)
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
    with n1: canone = st.number_input("Canone/Mese (Euro)", value=float(st.session_state["val_canone"]))
    with n2: anticipo = st.number_input("Anticipo (Euro)", value=float(st.session_state["val_anticipo"]))
    with n3: 
        idx_durata = [24, 36, 48, 60].index(st.session_state["val_durata"]) if st.session_state["val_durata"] in [24, 36, 48, 60] else 1
        durata = st.selectbox("Durata (Mesi)", [24, 36, 48, 60], index=idx_durata)
    with n4: km = st.number_input("Km/Anno", value=int(st.session_state["val_km"]))

    st.markdown("---")
    # --- LOGICA MULTI-PREVENTIVO ---
    if st.button("➕ AGGIUNGI AL DOCUMENTO"):
        foto_bytes = foto_m.getvalue() if foto_m else None
        auto_aggiunta = {
            "cliente": nome_cliente, "consegna": consegna, "t_veicolo": t_veicolo, "note": note_p,
            "marca": marca_stampa, "versione": versione_stampa, "foto_bytes": foto_bytes,
            "p_rca": p_rca, "p_if": p_if, "p_kasko": p_kasko, "infort": infort, "g_num": g_num,
            "canone": canone, "anticipo": anticipo, "durata": durata, "km": km
        }
        st.session_state["lista_preventivi"].append(auto_aggiunta)
        st.success(f"✅ Veicolo aggiunto! (Totale: {len(st.session_state['lista_preventivi'])} veicoli)")

    if len(st.session_state["lista_preventivi"]) > 0:
        st.info(f"🛒 Hai aggiunto **{len(st.session_state['lista_preventivi'])}** veicoli al preventivo congiunto.")
        
        col_stampa, col_svuota = st.columns([2, 1])
        with col_svuota:
            if st.button("🗑️ Svuota Lista"):
                st.session_state["lista_preventivi"] = []
                st.rerun()
                
        with col_stampa:
            if st.button("🚀 STAMPA PREVENTIVO UNICO (PDF MULTIPLO)"):
                st.markdown("""
                    <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
                        <style>@keyframes fall { 0% { transform: translateY(-10vh); opacity: 1; } 100% { transform: translateY(110vh); opacity: 0; } } .car { position: absolute; font-size: 40px; animation: fall 2s linear forwards; }</style>
                        <div class="car" style="left: 10%;">🚗</div><div class="car" style="left: 30%;">🚙</div><div class="car" style="left: 50%;">🚗</div><div class="car" style="left: 70%;">🚙</div><div class="car" style="left: 90%;">🚗</div>
                    </div>""", unsafe_allow_html=True)

                pdf = MaldarizziPDF()
                data_it = datetime.now().strftime('%d %B %Y').upper()
                
                for p in st.session_state["lista_preventivi"]:
                    pdf.add_page()
                    pdf.set_text_color(255, 255, 255)
                    
                    pdf.set_y(58)
                    pdf.set_font(pdf.f_f, "", 9)
                    pdf.cell(0, 5, f"{data_it} - VALIDITÀ {g_validita} GIORNI", align="C", ln=True)
                    pdf.set_font(pdf.f_f, "B", 12)
                    pdf.cell(0, 8, f"SPETT.LE {p['cliente'].upper()}", align="C", ln=True)

                    y_pos = 85
                    f_path = "tmp_multi.png"
                    if p["foto_bytes"]:
                        with open(f_path, "wb") as f: f.write(p["foto_bytes"])
                    else:
                        f_path = f"foto_vetture/{p['marca'].upper()}.jpg"
                    
                    if os.path.exists(f_path):
                        pdf.image(f_path, 110, y_pos, 90)
                    
                    pdf.set_xy(15, y_pos)
                    pdf.set_font(pdf.f_f, "B", 20)
                    pdf.multi_cell(90, 8, p['marca'].upper())
                    pdf.set_x(15)
                    pdf.set_font(pdf.f_f, "", 11)
                    pdf.multi_cell(90, 5, p['versione'])
                    
                    pdf.ln(4)
                    pdf.set_font(pdf.f_f, "B", 10)
                    pdf.set_x(15)
                    pdf.cell(90, 6, f"STATO: {p['t_veicolo'].upper()} ({p['consegna']})", ln=True)
                    pdf.set_x(15)
                    pdf.cell(90, 6, f"DURATA CONTRATTO: {p['durata']} MESI", ln=True)
                    pdf.set_x(15)
                    pdf.cell(90, 6, f"KM/ANNO: {p['km']:,} KM".replace(",", "."), ln=True)

                    pdf.set_y(155)
                    pdf.set_font(pdf.f_f, "B", 11)
                    pdf.cell(0, 7, "SERVIZI INCLUSI NEL CANONE", ln=True, align="C")
                    pdf.set_font(pdf.f_f, "", 9)
                    
                    serv_list = [
                        f"RCA (Franchigia {p['p_rca']})", 
                        f"Incendio/Furto (Franchigia {p['p_if']})",
                        f"Danni/Kasko (Franchigia {p['p_kasko']})",
                        "Manutenzione Ordinaria/Straordinaria",
                        "Assistenza Stradale H24"
                    ]
                    if p['g_num']: serv_list.append(f"Gomme: {p['g_num']}")
                    if p['infort']: serv_list.append("Infortunio Conducente (PAI)")
                    
                    pdf.multi_cell(0, 5, " | ".join(serv_list), align="C")
                    
                    pdf.ln(2)
                    pdf.set_font(pdf.f_f, "I", 8)
                    pdf.set_text_color(220, 220, 220)
                    pdf.cell(0, 5, "*Le immagini sono puramente indicative e non costituiscono vincolo contrattuale.", align="C", ln=True)

                    pdf.set_y(210)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font(pdf.f_f, "B", 28)
                    pdf.cell(0, 15, f"EURO {p['canone']}/MESE", align="C", ln=True)
                    pdf.set_font(pdf.f_f, "B", 14)
                    pdf.cell(0, 8, f"Anticipo: Euro {p['anticipo']} (Iva Esclusa)", align="C", ln=True)

                    if p['note']:
                        pdf.ln(2)
                        pdf.set_font(pdf.f_f, "I", 9)
                        pdf.multi_cell(0, 5, f"Note: {p['note']}", align="C")

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

                pdf.output("preventivo_multiplo.pdf")
                with open("preventivo_multiplo.pdf", "rb") as f:
                    st.download_button("📩 SCARICA IL PREVENTIVO CONGIUNTO", f, f"Offerta_Multipla.pdf", key="dl_multi")
