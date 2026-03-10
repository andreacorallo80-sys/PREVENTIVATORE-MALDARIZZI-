import streamlit as st
import pandas as pd
import os
import re
import pypdf
import io
from fpdf import FPDF
from datetime import datetime
import locale

# --- FUNZIONE PULIZIA TESTO ---
def pulisci_testo(testo):
    if not testo: return ""
    testo = str(testo)
    sostituzioni = {
        '€': 'Euro', '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2022': '-', '\xa0': ' ', '\t': ' ', '\r': ''
    }
    for k, v in sostituzioni.items():
        testo = testo.replace(k, v)
    return testo.encode('latin-1', 'ignore').decode('latin-1')

# --- DATABASE VENDITORI COMPLETO ---
DATABASE_UTENTI = {
    "v.catino": {"pw": "Maldarizzi2026", "nome": "VANESSA CATINO", "email": "v.catino@maldarizzi.com", "tel": "366 449 1633", "ruolo": "interno"},
    "f.manuto": {"pw": "Maldarizzi2026", "nome": "FRANCESCO MANUTO", "email": "f.manuto@maldarizzi.com", "tel": "342 353 1514", "ruolo": "interno"},
    "a.corallo": {"pw": "Maldarizzi2026", "nome": "ANDREA CORALLO", "email": "a.corallo@maldarizzi.com", "tel": "344 343 4826", "ruolo": "interno"},
    "g.delvecchio": {"pw": "Maldarizzi2026", "nome": "GRAZIA DEL VECCHIO", "email": "g.delvecchio@maldarizzi.com", "tel": "320 764 6334", "ruolo": "interno"},
    "a.pierro": {"pw": "Maldarizzi2026", "nome": "ANGELA PIERRO", "email": "a.pierro@maldarizzi.com", "tel": "388 928 5242", "ruolo": "interno"},
    "s.carlucci": {"pw": "Maldarizzi2026", "nome": "SAVERIO CARLUCCI", "email": "saverio.carlucci@maldarizzi.com", "tel": "337 232 984", "ruolo": "interno"},
    "l.grieco": {"pw": "Maldarizzi2026", "nome": "LUCA GRIECO", "email": "l.grieco@maldarizzi.com", "tel": "345 252 4566", "ruolo": "interno"},
    "m.schiralli": {"pw": "Maldarizzi2026", "nome": "MICHELE SCHIRALLI", "email": "m.schiralli@maldarizzi.com", "tel": "327 681 0137", "ruolo": "interno"},
    "d.catanzaro": {"pw": "Maldarizzi2026", "nome": "DORIANA CATANZARO", "email": "d.catanzaro@maldarizzi.com", "tel": "349 756 8629", "ruolo": "interno"},
    "v.schiralli": {"pw": "Maldarizzi2026", "nome": "VINCENZO SCHIRALLI", "email": "v.schiralli@maldarizzi.com", "tel": "327 681 0137", "ruolo": "interno"},
    "a.lozito": {"pw": "Maldarizzi2026", "nome": "ALESSANDRA LOZITO", "email": "a.lozito@maldarizzi.com", "tel": "340 450 7513", "ruolo": "interno"},
    "p.nolli": {"pw": "Maldarizzi2026", "nome": "PASQUALE NOLLI", "email": "pasquale@omniaprima.com", "tel": "331 399 3389", "ruolo": "interno"},
    "admin": {"pw": "cipiacemigliorare", "nome": "ADMIN MALDARIZZI", "email": "admin@admin.com", "tel": "000 0000000", "ruolo": "interno"}
}

# --- 1. FUNZIONE LOGIN ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["current_user"] = None

    if not st.session_state["authenticated"]:
        st.markdown("<style>.stApp { background-color: #000000; }</style>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if os.path.exists("logo.png"): 
                st.image("logo.png", width=200)
            st.subheader("Portale Noleggio Maldarizzi")
            user = st.text_input("Username (es. v.catino)").lower().strip()
            password = st.text_input("Password", type="password")
            if st.button("Accedi"):
                if user in DATABASE_UTENTI and password == DATABASE_UTENTI[user]["pw"]:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = DATABASE_UTENTI[user]
                    st.rerun()
                else:
                    st.error("Credenziali errate")
        return False
    return True

# --- INIZIALIZZAZIONE VARIABILI IN MEMORIA (PER IL PREVENTIVATORE E MENU) ---
if "menu_scelta" not in st.session_state: st.session_state["menu_scelta"] = "🔥 Offerte del Mese"
if "lista_preventivi" not in st.session_state: st.session_state["lista_preventivi"] = []
if "val_canone" not in st.session_state: st.session_state["val_canone"] = 500.0
if "val_durata" not in st.session_state: st.session_state["val_durata"] = 36
if "val_km" not in st.session_state: st.session_state["val_km"] = 15000
if "val_anticipo" not in st.session_state: st.session_state["val_anticipo"] = 0.0
if "val_cliente" not in st.session_state: st.session_state["val_cliente"] = "Gentile CLIENTE"
if "val_tipo_cliente" not in st.session_state: st.session_state["val_tipo_cliente"] = "Partita IVA"
if "val_input_mode" not in st.session_state: st.session_state["val_input_mode"] = "Testo Libero"
if "val_marca_stampa" not in st.session_state: st.session_state["val_marca_stampa"] = ""
if "val_versione_stampa" not in st.session_state: st.session_state["val_versione_stampa"] = ""
if "val_opt" not in st.session_state: st.session_state["val_opt"] = "" 
if "val_p_rca" not in st.session_state: st.session_state["val_p_rca"] = "250 Euro"
if "val_p_if" not in st.session_state: st.session_state["val_p_if"] = "10%"
if "val_p_kasko" not in st.session_state: st.session_state["val_p_kasko"] = "500 Euro"
if "debug_text" not in st.session_state: st.session_state["debug_text"] = ""
if "val_note" not in st.session_state: st.session_state["val_note"] = ""

# --- 2. CLASSE PDF ---
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
        if os.path.exists("sfondo_nero.jpg"):
            try:
                self.image("sfondo_nero.jpg", 0, 0, 210, 297)
            except Exception:
                self.set_fill_color(20, 20, 20)
                self.rect(0, 0, 210, 297, 'F')
        else:
            self.set_fill_color(20, 20, 20)
            self.rect(0, 0, 210, 297, 'F')

        if os.path.exists("logo.png"):
            try:
                self.image("logo.png", 5, 5, 45) 
            except Exception: pass

        if os.path.exists("logo.png"):
            try:
                self.image("logo.png", 145, 275, 55)
            except Exception: pass

# ==========================================
# AVVIO APP PRINCIPALE
# ==========================================
st.set_page_config(page_title="Portale Maldarizzi", layout="wide")
try: locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
except: pass

if check_password():
    utente_loggato = st.session_state["current_user"]
    
    # --- MENU DI NAVIGAZIONE LATERALE ---
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", width=180)
        
    st.sidebar.markdown(f"👤 Benvenuto, **{utente_loggato['nome']}**")
    st.sidebar.markdown(f"🏷️ Ruolo: *{utente_loggato['ruolo'].upper()}*")
    st.sidebar.markdown("---")
    
    # Il Radio button ora è legato alla variabile di sessione (permette il salto automatico)
    menu_scelta = st.sidebar.radio("📌 MENU PRINCIPALE", ["🔥 Offerte del Mese", "🎯 Preventivatore Strumentale"], key="menu_scelta")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Esci"):
        st.session_state["authenticated"] = False
        st.rerun()

    # ==========================================
    # SEZIONE 1: DASHBOARD PROMO (VETRINA DA EXCEL)
    # ==========================================
    if st.session_state["menu_scelta"] == "🔥 Offerte del Mese":
        st.title("🔥 Promozioni del Mese")
        st.markdown("Sfoglia le offerte, verifica i dettagli e trasferiscile nel preventivatore con un clic.")
        
        # UPLOAD DEL FILE EXCEL PROMO
        st.sidebar.header("📥 Gestione Database Promo")
        file_promo = st.sidebar.file_uploader("Carica il file Excel delle promozioni", type=["xlsx", "csv"])
        if file_promo:
            with open("promo_mese.xlsx", "wb") as f: 
                f.write(file_promo.getbuffer())
            st.sidebar.success("✅ Database Promozioni aggiornato!")

        if os.path.exists("promo_mese.xlsx"):
            try:
                df_promo = pd.read_excel("promo_mese.xlsx")
                # Pulizia severa degli spazi nei nomi delle colonne
                df_promo.columns = df_promo.columns.str.strip()
                df_promo = df_promo.fillna("") 
                
                c_search, c_alimen = st.columns([2, 1])
                with c_search:
                    ricerca = st.text_input("🔍 Cerca per marca o modello...").upper()
                with c_alimen:
                    # Se non esiste la colonna alimentazione la saltiamo
                    if 'ALIMENTAZIONE' in df_promo.columns:
                        lista_alimen = ["Tutte"] + sorted([str(x).upper() for x in df_promo['ALIMENTAZIONE'].unique() if x])
                        filtro_alimen = st.selectbox("⚡ Alimentazione", lista_alimen)
                    else:
                        filtro_alimen = "Tutte"
                
                st.markdown("---")
                
                offerte_filtrate = []
                for _, row in df_promo.iterrows():
                    marca = str(row.get('MARCA', '')).strip().upper()
                    modello = str(row.get('MODELLO', '')).strip()
                    
                    if 'ALIMENTAZIONE' in df_promo.columns:
                        alimen = str(row.get('ALIMENTAZIONE', '')).strip().upper()
                    else:
                        alimen = ""

                    # Lettura nuovi campi richiesti
                    offerta_tipo = str(row.get('OFFERTA', '')).strip()
                    player = str(row.get('PLAYER', '')).strip().upper()
                    commissioni = str(row.get('COMMISSIONI', '')).strip()
                    link_offerta = str(row.get('link offerta', '')).strip()
                    
                    try: canone = int(float(str(row.get('CANONE', 0)).replace(',','.')))
                    except: canone = 0
                    try: anticipo = int(float(str(row.get('ANTICIPO', 0)).replace(',','.')))
                    except: anticipo = 0
                    try: mesi = int(row.get('MESI', 0))
                    except: mesi = 0
                    try: km = int(row.get('KM TOTALI', 0))
                    except: km = 0

                    if ricerca and ricerca not in marca and ricerca not in modello.upper():
                        continue
                    if filtro_alimen != "Tutte" and alimen != filtro_alimen:
                        continue
                        
                    offerte_filtrate.append({
                        "marca": marca, "modello": modello, "canone": canone, 
                        "anticipo": anticipo, "durata": mesi, "km": km,
                        "tipo": offerta_tipo, "player": player, "comm": commissioni, "link": link_offerta
                    })
                
                if not offerte_filtrate:
                    st.warning("Nessuna offerta trovata con questi parametri.")
                else:
                    colonne_griglia = st.columns(3)
                    for idx, auto in enumerate(offerte_filtrate):
                        with colonne_griglia[idx % 3]:
                            # Costruiamo il blocco HTML per mostrare i dati tecnici
                            link_html = f'<a href="{auto["link"]}" target="_blank" style="color: #C9BC41; text-decoration: none; font-size: 13px;">🔗 Apri pagina Offerta</a>' if auto["link"] else ""
                            
                            st.markdown(f"""
                            <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px;">
                                <h3 style="margin-bottom: 0; color: #FFF;">{auto['marca']}</h3>
                                <h5 style="margin-top: 0; color: #AAA;">{auto['modello']}</h5>
                                <h1 style="color: #C9BC41; margin-bottom: 5px;">€ {auto['canone']}<span style="font-size: 14px; color: #888;"> /mese</span></h1>
                                <p style="color: #DDD; font-size: 14px; margin-bottom: 10px;">
                                    ⏳ {auto['durata']} mesi | 🛣️ {auto['km']} Km totali<br>
                                    💰 Anticipo: € {auto['anticipo']}
                                </p>
                                <hr style="border-top: 1px solid #444; margin: 10px 0;">
                                <p style="font-size: 13px; color: #BBB; line-height: 1.4; margin-bottom: 5px;">
                                    🏢 <b>Player:</b> {auto['player']}<br>
                                    🏷️ <b>Tipo:</b> {auto['tipo']}<br>
                                    💶 <b>Commissioni:</b> {auto['comm']}
                                </p>
                                {link_html}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # IL BOTTONE MAGICO: TRASFERISCE I DATI E CAMBIA SCHERMATA
                            if st.button(f"➡️ Usa Promo {auto['marca']}", key=f"btn_promo_{idx}"):
                                st.session_state["val_marca_stampa"] = auto['marca']
                                st.session_state["val_versione_stampa"] = auto['modello']
                                st.session_state["val_canone"] = float(auto['canone'])
                                st.session_state["val_anticipo"] = float(auto['anticipo'])
                                st.session_state["val_durata"] = auto['durata']
                                st.session_state["val_km"] = auto['km']
                                st.session_state["val_input_mode"] = "Testo Libero"
                                # Salta alla pagina Preventivatore
                                st.session_state["menu_scelta"] = "🎯 Preventivatore Strumentale"
                                st.rerun()

            except Exception as e:
                st.error(f"Si è verificato un errore nella lettura del file Excel: {str(e)}")
        else:
            st.info("👈 Carica il file Excel delle promozioni dal menù laterale per generare la vetrina.")


    # ==========================================
    # SEZIONE 2: PREVENTIVATORE STRUMENTALE
    # ==========================================
    elif st.session_state["menu_scelta"] == "🎯 Preventivatore Strumentale":
        st.title("🎯 Preventivatore Strumentale")
        
        st.sidebar.header("📥 Importa PDF Portale")
        pdf_portale = st.sidebar.file_uploader("Carica PDF (Arval, Leasys, Ayvens)", type=["pdf"])
        
        if pdf_portale and st.sidebar.button("🧠 Analizza e Compila Dati dal PDF"):
            try:
                pdf_bytes = io.BytesIO(pdf_portale.getvalue())
                reader = pypdf.PdfReader(pdf_bytes)
                
                testo_estratto = ""
                for page in reader.pages:
                    t = page.extract_text()
                    if t: testo_estratto += t + " \n "
                
                testo_flat = re.sub(r'\s+', ' ', testo_estratto).strip()
                testo_upper = testo_flat.upper()
                st.session_state["debug_text"] = testo_flat
                st.session_state["val_input_mode"] = "Testo Libero"
                
                if "IVA INCLUSA" in testo_upper or "I.V.A. INCLUSA" in testo_upper or "CODICE FISCALE" in testo_upper or "C.F." in testo_upper or "PRIVATO" in testo_upper:
                    st.session_state["val_tipo_cliente"] = "Privato"
                else:
                    st.session_state["val_tipo_cliente"] = "Partita IVA"

                brands = ['FIAT', 'CITROEN', 'FORD', 'AUDI', 'BMW', 'MERCEDES', 'VOLKSWAGEN', 'PEUGEOT', 'RENAULT', 'OPEL', 'ALFA ROMEO', 'JEEP', 'TOYOTA', 'NISSAN', 'VOLVO', 'KIA', 'HYUNDAI', 'DACIA', 'LANCIA', 'SEAT', 'CUPRA', 'SUZUKI', 'MAZDA', 'LAND ROVER', 'PORSCHE', 'TESLA', 'MINI', 'LEXUS', 'MASERATI', 'SMART', 'SKODA', 'HONDA', 'MG', 'DS', 'IVECO']

                # --- AYVENS ---
                if "AYVENS" in testo_upper or "SOCIETE GENERALE" in testo_upper or "ALD AUTOMOTIVE" in testo_upper:
                    m_cli = re.search(r':\s*([A-Za-z\s\,\'\.\-]+?)\s*\d{6,9}/\d{2,3}', testo_flat)
                    if m_cli: 
                        nome_raw = m_cli.group(1).strip()
                        if "," in nome_raw:
                            nome_raw = nome_raw.split(",")[0].strip()
                            parti = nome_raw.split()
                            if len(parti) > 2 and parti[-1] == parti[-2]:
                                nome_raw = " ".join(parti[:-1])
                        st.session_state["val_cliente"] = nome_raw.upper()

                    m_vei = re.search(r'Veicolo:\s*(.*?)\s*Codici:', testo_flat, re.IGNORECASE)
                    if not m_vei:
                        m_vei = re.search(r'Venduto\s+(?:OFFERTA\s+[A-Z]+\s+|[A-Z0-9]+\s+)?(.*?)\s+\d{2}/\d{2}/\d{4}', testo_flat, re.IGNORECASE)
                    
                    if m_vei:
                        vei = m_vei.group(1).strip()
                        if vei.endswith('.'): vei = vei[:-1].strip()
                        st.session_state["val_versione_stampa"] = vei
                        marca_trovata = vei.split()[0].upper()
                        for b in brands:
                            if vei.upper().startswith(b):
                                marca_trovata = b
                                break
                        st.session_state["val_marca_stampa"] = marca_trovata

                    m_dur_km = re.search(r'\b(24|36|48|60)\s+(\d{4,7})\s+€', testo_flat)
                    if m_dur_km:
                        st.session_state["val_durata"] = int(m_dur_km.group(1))
                        km_tot = int(m_dur_km.group(2))
                        if st.session_state["val_durata"] > 0:
                            st.session_state["val_km"] = int((km_tot / st.session_state["val_durata"]) * 12)

                    m_can = re.findall(r'€\s*(\d{2,4}[,.]\d{2})', testo_flat)
                    if m_can:
                        valori = sorted([float(c.replace(',', '.')) for c in m_can], reverse=True)
                        if len(valori) > 0:
                            massimo = valori[0]
                            prezzo_corretto = massimo
                            for v in valori:
                                if abs(massimo - (v * 1.22)) < 1.0: 
                                    prezzo_corretto = v
                                    break
                            st.session_state["val_canone"] = prezzo_corretto
                    
                    m_ant = re.search(r'Anticipo\s*\(iva\s*esclusa\)\s*€\s*(\d{1,6}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_ant: st.session_state["val_anticipo"] = float(m_ant.group(1).replace(',', '.'))

                # --- LEASYS ---
                elif "LEASYS" in testo_upper:
                    m_cli = re.search(r'VENDITA\s+(.*?)\s+MALDARIZZI', testo_flat, re.IGNORECASE)
                    if m_cli: st.session_state["val_cliente"] = m_cli.group(1).replace("SRL", "").replace("SPA", "").strip()

                    m_marca = re.search(r'Marca\s+([A-Za-z0-9\-]+)', testo_flat, re.IGNORECASE)
                    if m_marca: st.session_state["val_marca_stampa"] = m_marca.group(1).upper().strip()
                    
                    m_ver = re.search(r'Versione\s+(.*?)\s+Canone Totale', testo_flat, re.IGNORECASE)
                    if m_ver: st.session_state["val_versione_stampa"] = m_ver.group(1).strip()

                    m_dur = re.search(r'Durata\s+(\d{2,3})', testo_flat, re.IGNORECASE)
                    if m_dur: st.session_state["val_durata"] = int(m_dur.group(1))

                    m_km = re.search(r'km totali\s+([\d\s]+)\b', testo_flat, re.IGNORECASE)
                    if m_km:
                        km_tot = int(m_km.group(1).replace(' ', ''))
                        if st.session_state["val_durata"] > 0:
                            st.session_state["val_km"] = int((km_tot / st.session_state["val_durata"]) * 12)

                    m_can = re.search(r'Canone Totale\s+€\s*(\d{1,4}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_can: st.session_state["val_canone"] = float(m_can.group(1).replace(',', '.'))
                        
                    m_ant = re.search(r'Anticipo\s*€\s*([\d\s]+[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_ant:
                        valore_pulito = m_ant.group(1).replace(' ', '').replace(',', '.')
                        st.session_state["val_anticipo"] = float(valore_pulito)
                    
                    m_fran = re.search(r'Franchigia km\s+([\d\s]+)\b', testo_flat, re.IGNORECASE)
                    if m_fran:
                        franchigia_km = int(m_fran.group(1).replace(' ', ''))
                        if franchigia_km > 0:
                            st.session_state["val_note"] = f"Nota bene: il contratto include {franchigia_km} km di franchigia aggiuntivi da sommare al totale."

                # --- ARVAL ---
                elif "ARVAL" in testo_upper:
                    m_cli = re.search(r'Ragione Sociale\s+([A-Za-z0-9\s\&\.\'\-]+?)\s+(?:CF Cliente|C\.F\.|Codice\s*Fiscale|P\.?IVA|Partita\s*IVA)', testo_flat, re.IGNORECASE)
                    if m_cli: st.session_state["val_cliente"] = m_cli.group(1).strip().upper()
                    
                    m_vei = re.search(r'per il veicolo\s+(.*?)\s+Canone', testo_flat, re.IGNORECASE)
                    if m_vei:
                        vei = m_vei.group(1).strip()
                        st.session_state["val_versione_stampa"] = vei
                        marca_trovata = vei.split()[0].upper()
                        for b in brands:
                            if vei.upper().startswith(b):
                                marca_trovata = b
                                break
                        st.session_state["val_marca_stampa"] = marca_trovata

                    m_can = re.search(r'Canone\s+(\d{1,4}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_can: st.session_state["val_canone"] = float(m_can.group(1).replace(',', '.'))

                    m_dur = re.search(r'durata\s+(\d{2,3})\s*mesi', testo_flat, re.IGNORECASE)
                    if m_dur: st.session_state["val_durata"] = int(m_dur.group(1))

                    m_km = re.search(r'km totali\s+(\d{2,6})', testo_flat, re.IGNORECASE)
                    if m_km:
                        km_tot = int(m_km.group(1))
                        durata = st.session_state.get("val_durata", 36)
                        if durata > 0:
                            st.session_state["val_km"] = int((km_tot / durata) * 12)

                    m_ant = re.search(r'Anticipo\s*(?:€|Euro)?\s*(\d{1,6}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_ant: st.session_state["val_anticipo"] = float(m_ant.group(1).replace(',', '.'))

                if "500" in testo_flat and ("Danni" in testo_flat or "Kasko" in testo_flat): st.session_state["val_p_kasko"] = "500 Euro"
                elif "1000" in testo_flat: st.session_state["val_p_kasko"] = "1000 Euro"
                elif "249" in testo_flat: st.session_state["val_p_kasko"] = "250 Euro" 
                
                if "250" in testo_flat and "RCA" in testo_flat: st.session_state["val_p_rca"] = "250 Euro"
                elif "500" in testo_flat and "RCA" in testo_flat: st.session_state["val_p_rca"] = "500 Euro"
                
                if "10%" in testo_flat: st.session_state["val_p_if"] = "10%"
                elif "5%" in testo_flat: st.session_state["val_p_if"] = "5%"
                elif "500" in testo_flat and ("Incendio" in testo_flat or "Furto" in testo_flat): st.session_state["val_p_if"] = "500 Euro"
                elif "250" in testo_flat and ("Incendio" in testo_flat or "Furto" in testo_flat): st.session_state["val_p_if"] = "250 Euro"

                st.sidebar.success("✅ Dati estratti chirurgicamente!")
                st.rerun()
                
            except Exception as e:
                st.session_state["debug_text"] = testo_flat if 'testo_flat' in locals() else f"Errore: {str(e)}"
                st.sidebar.error(f"Errore durante l'analisi del PDF: {str(e)}")

        if st.session_state.get("debug_text"):
            with st.sidebar.expander("🛠️ Mostra Testo Letto dal PDF (Debug)"):
                st.write(st.session_state["debug_text"])

        st.sidebar.markdown("---")
        st.sidebar.header("📁 Database Listino")
        uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"], key="listino_upload")
        if uploaded_excel:
            with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
            st.sidebar.success("Database aggiornato!")

        if os.path.exists("dati.xlsx"):
            excel = pd.ExcelFile("dati.xlsx")
            foglio = st.sidebar.selectbox("Seleziona Categoria", excel.sheet_names)
            df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
        else:
            st.sidebar.warning("Carica dati.xlsx per ricerca da listino")
        
        st.sidebar.markdown("---")
        g_validita = st.sidebar.slider("Validità Offerta (gg)", 1, 30, 30)

        nome_cons = utente_loggato["nome"]
        email_cons = utente_loggato["email"]
        tel_cons = utente_loggato["tel"]

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("👤 Cliente")
            idx_tipo_cli = 1 if st.session_state.get("val_tipo_cliente", "Partita IVA") == "Privato" else 0
            tipo_cliente = st.radio("Tipologia", ["Partita IVA", "Privato"], index=idx_tipo_cli, horizontal=True)
            nome_cliente = st.text_input("Nome Cliente", value=st.session_state.get("val_cliente", ""))
            consegna = st.selectbox("Luogo Consegna", ["IN SEDE MALDARIZZI", "A DOMICILIO"])
            t_veicolo = st.radio("Stato Veicolo (Stampa)", ["Nuovo", "Usato"], horizontal=True)
            note_p = st.text_area("Note aggiuntive", value=st.session_state.get("val_note", ""), height=70)
        
        with c2:
            st.subheader("🚘 Veicolo")
            idx_input_mode = 1 if st.session_state.get("val_input_mode") == "Testo Libero" else 0
            input_mode = st.radio("Modalità Inserimento", ["Da Listino", "Testo Libero"], horizontal=True, index=idx_input_mode)
            
            if input_mode == "Testo Libero" or not os.path.exists("dati.xlsx"):
                marca_stampa = st.text_input("Marca", value=st.session_state.get("val_marca_stampa", ""))
                versione_stampa = st.text_area("Allestimento/Versione", value=st.session_state.get("val_versione_stampa", ""))
            else:
                marca_sel = st.selectbox("Marca", sorted(df['Brand Description'].unique().tolist()))
                modello_sel = st.selectbox("Modello (Filtro)", sorted(df[df['Brand Description']==marca_sel]['Vehicle Set description'].unique().tolist()))
                versione_sel = st.selectbox("Versione/Allestimento", sorted(df[(df['Brand Description']==marca_sel) & (df['Vehicle Set description']==modello_sel)]['Jato Product Description'].unique().tolist()))
                marca_stampa = marca_sel
                versione_stampa = versione_sel
            
            opt_p = st.text_area("Optional Vettura", value=st.session_state.get("val_opt", ""), height=70)
            foto_m = st.file_uploader("Foto Auto (Opzionale)", type=["jpg", "png", "jpeg"])

        st.markdown("---")
        st.subheader("🛡️ Servizi e Penali")
        s1, s2, s3 = st.columns(3)
        
        with s1:
            rca_options = ["0 Euro", "250 Euro", "500 Euro"]
            rca_idx = rca_options.index(st.session_state.get("val_p_rca", "250 Euro")) if st.session_state.get("val_p_rca", "250 Euro") in rca_options else 1
            p_rca = st.selectbox("Penale RCA", rca_options, index=rca_idx)
            
            if_options = ["0%", "5%", "10%", "250 Euro", "500 Euro"]
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
        
        iva_text = "Iva Inclusa" if tipo_cliente == "Privato" else "Iva Esclusa"
        
        with n1: canone = st.number_input(f"Canone/Mese ({iva_text})", value=float(st.session_state["val_canone"]))
        with n2: anticipo = st.number_input(f"Anticipo ({iva_text})", value=float(st.session_state["val_anticipo"]))
        with n3: 
            durate_disp = [24, 36, 48, 60]
            valore_durata = int(st.session_state.get("val_durata", 36))
            if valore_durata not in durate_disp: durate_disp.append(valore_durata)
            durata = st.selectbox("Durata (Mesi)", sorted(durate_disp), index=sorted(durate_disp).index(valore_durata))
        with n4: km = st.number_input("Km/Anno", value=int(st.session_state["val_km"]))

        st.markdown("---")
        if st.button("➕ AGGIUNGI AL DOCUMENTO"):
            foto_bytes = foto_m.getvalue() if foto_m else None
            auto_aggiunta = {
                "cliente": pulisci_testo(nome_cliente), "consegna": pulisci_testo(consegna), 
                "t_veicolo": pulisci_testo(t_veicolo), "note": pulisci_testo(note_p),
                "opt": pulisci_testo(opt_p), 
                "marca": pulisci_testo(marca_stampa), "versione": pulisci_testo(versione_stampa), 
                "foto_bytes": foto_bytes, "p_rca": pulisci_testo(p_rca), "p_if": pulisci_testo(p_if), 
                "p_kasko": pulisci_testo(p_kasko), "infort": infort, "g_num": pulisci_testo(g_num) if g_num else None,
                "canone": canone, "anticipo": anticipo, "durata": durata, "km": km,
                "iva_text": iva_text 
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
                if st.button("🚀 STAMPA PREVENTIVO UNICO (DESIGN UFFICIALE)"):
                    st.markdown("""
                        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;">
                            <style>@keyframes fall { 0% { transform: translateY(-10vh); opacity: 1; } 100% { transform: translateY(110vh); opacity: 0; } } .car { position: absolute; font-size: 40px; animation: fall 2s linear forwards; }</style>
                            <div class="car" style="left: 10%;">🚗</div><div class="car" style="left: 30%;">🚙</div><div class="car" style="left: 50%;">🚗</div><div class="car" style="left: 70%;">🚙</div><div class="car" style="left: 90%;">🚗</div>
                        </div>""", unsafe_allow_html=True)

                    pdf = MaldarizziPDF()
                    
                    for i, p in enumerate(st.session_state["lista_preventivi"]):
                        pdf.add_page()
                        
                        pdf.set_y(20)
                        pdf.set_font(pdf.f_f, "", 12)
                        pdf.set_text_color(200, 200, 200)
                        pdf.cell(0, 5, "Spettabile cliente:", align="C", ln=True)
                        
                        pdf.set_font(pdf.f_f, "B", 16)
                        pdf.set_text_color(255, 255, 255) 
                        pdf.cell(0, 7, pulisci_testo(p['cliente'].upper()), align="C", ln=True)
                        
                        pdf.set_y(45)
                        pdf.set_font(pdf.f_f, "B", 24)
                        pdf.set_text_color(255, 255, 255)
                        titolo_auto = pulisci_testo(f"{p['marca']} {p['versione']}")
                        pdf.multi_cell(0, 10, titolo_auto, align="C")
                        
                        y_img = pdf.get_y() + 2
                        if p["foto_bytes"]:
                            f_path = f"tmp_multi_{i}.png" 
                            with open(f_path, "wb") as f: f.write(p["foto_bytes"])
                        else:
                            f_path = f"foto_vetture/{p['marca'].upper()}.jpg"
                        
                        if os.path.exists(f_path):
                            try: pdf.image(f_path, 25, y_img, 160)
                            except Exception: pass
                        
                        pdf.set_y(155)
                        pdf.set_font(pdf.f_f, "B", 50) 
                        pdf.set_text_color(201, 188, 65) 
                        
                        canone_str = str(p['canone'])
                        if canone_str.endswith(".0"): canone_str = canone_str[:-2]
                        
                        pdf.cell(0, 15, pulisci_testo(f"Euro {canone_str} / mese"), align="C", ln=True)
                        
                        pdf.set_y(180)
                        pdf.set_font(pdf.f_f, "B", 11)
                        pdf.set_text_color(255, 255, 255)
                        pdf.set_fill_color(40, 40, 40)
                        
                        km_tot = int(p['km']) * int(p['durata']) // 12
                        anticipo_str = str(p['anticipo'])
                        if anticipo_str.endswith(".0"): anticipo_str = anticipo_str[:-2]
                        
                        voci = [
                            f"{p['durata']} mesi", 
                            f"Km {km_tot}", 
                            f"Anticipo {anticipo_str}", 
                            p['iva_text'] 
                        ]
                        
                        larghezza_box = 42
                        spazio = 4
                        start_x = (210 - (larghezza_box * 4 + spazio * 3)) / 2
                        
                        for idx, voce in enumerate(voci):
                            x_pos = start_x + (larghezza_box + spazio) * idx
                            pdf.set_xy(x_pos, 180)
                            pdf.cell(larghezza_box, 10, pulisci_testo(voce), border=0, align="C", fill=True)
                        
                        pdf.set_y(202)
                        pdf.set_font(pdf.f_f, "B", 11)
                        pdf.set_text_color(255, 255, 255)
                        pdf.set_x(10)
                        pdf.cell(0, 6, pulisci_testo("SERVIZI INCLUSI NEL CANONE"), ln=True, align="C")
                        
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
                        
                        testo_servizi = " | ".join(serv_list)
                        pdf.set_x(10)
                        pdf.multi_cell(0, 5, pulisci_testo(testo_servizi), align="C")

                        if p.get('opt'):
                            pdf.ln(2)
                            pdf.set_font(pdf.f_f, "B", 10)
                            pdf.set_text_color(201, 188, 65)
                            pdf.set_x(10)
                            pdf.cell(0, 6, pulisci_testo("OPTIONAL INCLUSI"), ln=True, align="C")
                            pdf.set_font(pdf.f_f, "", 8)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_x(10)
                            pdf.multi_cell(0, 4, pulisci_testo(p['opt']), align="C")

                        pdf.ln(3)
                        pdf.set_font(pdf.f_f, "I", 8)
                        pdf.set_text_color(180, 180, 180) 
                        
                        pdf.set_x(10) 
                        pdf.multi_cell(0, 4, pulisci_testo("*Le immagini sono puramente indicative e non costituiscono vincolo contrattuale."), align="C")
                        pdf.set_x(10) 
                        pdf.multi_cell(0, 4, pulisci_testo("*ATTENZIONE: il canone indicato non comprende la tassa automobilistica, da gennaio 2020 a carico del cliente per modifica di legge (D.L. 124/2019)."), align="C")
                        pdf.set_x(10) 
                        pdf.multi_cell(0, 4, pulisci_testo(f"*La presente offerta ha una validità di {g_validita} giorni."), align="C")

                        if p['note']:
                            pdf.ln(2)
                            pdf.set_font(pdf.f_f, "B", 9)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_x(10)
                            pdf.multi_cell(0, 5, pulisci_testo(f"Note aggiuntive: {p['note']}"), align="C")

                        pdf.set_y(255)
                        pdf.set_font(pdf.f_f, "B", 10)
                        pdf.set_text_color(255, 255, 255)
                        pdf.set_x(10)
                        pdf.cell(0, 5, pulisci_testo(f"CONSULENTE: {nome_cons.upper()}"), align="C", ln=True)
                        
                        pdf.set_font(pdf.f_f, "", 9)
                        pdf.set_text_color(200, 200, 200)
                        pdf.set_x(10)
                        pdf.cell(0, 5, pulisci_testo(f"E-mail: {email_cons}  |  Tel: {tel_cons}"), align="C", ln=True)

                    pdf.output("preventivo_multiplo.pdf")
                    with open("preventivo_multiplo.pdf", "rb") as f:
                        st.download_button("📩 SCARICA PREVENTIVO (DESIGN UFFICIALE)", f, f"Offerta_Multipla.pdf", key="dl_multi")

