import streamlit as st
import pandas as pd
import os
import re
import pypdf
import io
import requests
from fpdf import FPDF
from datetime import datetime
import locale

# --- CREAZIONE CARTELLA CACHE PER RISPARMIARE CHIAMATE FOTO ---
if not os.path.exists("Foto_Cache"):
    os.makedirs("Foto_Cache")

# --- HELPER LETTURA FILE (Risolve problemi di virgole, punti e virgola o spazi) ---
def leggi_file_dati(percorso):
    if percorso.endswith(".csv"):
        try:
            df = pd.read_csv(percorso, sep=";")
            if len(df.columns) < 3: df = pd.read_csv(percorso, sep=",")
            return df
        except:
            df = pd.read_csv(percorso, sep=";", encoding="latin-1")
            if len(df.columns) < 3: df = pd.read_csv(percorso, sep=",", encoding="latin-1")
            return df
    else:
        return pd.read_excel(percorso)

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

# --- MOTORE FOTO (GOOGLE + CACHE) ---
def scarica_foto_auto_api(marca, versione):
    GOOGLE_API_KEY = "INSERISCI_QUI_LA_API_KEY_DI_GOOGLE"
    GOOGLE_CX = "INSERISCI_QUI_IL_CX_DI_GOOGLE"
    
    if GOOGLE_API_KEY == "INSERISCI_QUI_LA_API_KEY_DI_GOOGLE":
        return None

    marca_clean = str(marca).strip().title()
    parti_versione = str(versione).strip().split()
    modello_clean = parti_versione[0].title() if parti_versione else ""
    trim_clean = " ".join(parti_versione[1:]).title() if len(parti_versione) > 1 else ""
    
    nome_file_cache = f"Foto_Cache/{marca_clean}_{modello_clean}_{trim_clean}.jpg".replace(" ", "_").replace("/", "_").lower()
    
    if os.path.exists(nome_file_cache):
        with open(nome_file_cache, "rb") as f: return f.read()

    url_api = "https://www.googleapis.com/customsearch/v1"
    query_ricerca = f"{marca_clean} {modello_clean} {trim_clean} car exterior side view white background"
    
    parametri = {
        "q": query_ricerca, "cx": GOOGLE_CX, "key": GOOGLE_API_KEY,
        "searchType": "image", "imgSize": "LARGE", "num": 3
    }
    try:
        risposta = requests.get(url_api, params=parametri, timeout=10)
        if risposta.status_code == 200:
            dati_json = risposta.json()
            if "items" in dati_json and len(dati_json["items"]) > 0:
                for item in dati_json["items"]:
                    link_foto = item.get("link")
                    if link_foto:
                        try:
                            risposta_foto = requests.get(link_foto, timeout=5)
                            if risposta_foto.status_code == 200 and "image" in risposta_foto.headers.get("Content-Type", ""):
                                with open(nome_file_cache, "wb") as f: f.write(risposta_foto.content)
                                return risposta_foto.content
                        except: continue
    except Exception: pass
    return None

# --- REGISTRAZIONE STATISTICHE ---
def registra_statistica(consulente, cliente, marca, modello, canone, anticipo, durata, km, origine):
    file_path = "statistiche_preventivi.csv"
    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuovo_dato = pd.DataFrame([{
        "Data_Ora": data_ora, "Consulente": consulente, "Cliente": cliente,
        "Marca": marca, "Modello": modello, "Canone_Mese": canone,
        "Anticipo": anticipo, "Durata_Mesi": durata, "Km_Anno": km, "Sorgente_Dati": origine
    }])
    if os.path.exists(file_path): nuovo_dato.to_csv(file_path, mode='a', header=False, index=False)
    else: nuovo_dato.to_csv(file_path, mode='w', header=True, index=False)

# --- DATABASE VENDITORI ---
DATABASE_UTENTI = {
    "v.catino": {"pw": "Maldarizzi2026", "nome": "VANESSA CATINO", "email": "v.catino@maldarizzi.com", "tel": "366 449 1633", "ruolo": "interno"},
    "f.manuto": {"pw": "Maldarizzi2026", "nome": "FRANCESCO MANUTO", "email": "f.manuto@maldarizzi.com", "tel": "342 353 1514", "ruolo": "interno"},
    "a.corallo": {"pw": "Maldarizzi2026", "nome": "ANDREA CORALLO", "email": "a.corallo@maldarizzi.com", "tel": "344 343 4826", "ruolo": "interno"},
    "g.delvecchio": {"pw": "Maldarizzi2026", "nome": "GRAZIA DEL VECCHIO", "email": "g.delvecchio@maldarizzi.com", "tel": "320 764 6334", "ruolo": "interno"},
    "a.pierro": {"pw": "Maldarizzi2026", "nome": "ANGELA PIERRO", "email": "a.pierro@maldarizzi.com", "tel": "388 928 5242", "ruolo": "interno"},
    "s.carlucci": {"pw": "Maldarizzi2026", "nome": "SAVERIO CARLUCCI", "email": "saverio.carlucci@maldarizzi.com", "tel": "337 232 984", "ruolo": "interno"},
    "l.grieco": {"pw": "Maldarizzi2026", "nome": "LUCA GRIECO", "email": "l.grieco@maldarizzi.com", "tel": "345 252 4566", "ruolo": "interno"},
    "m.schiralli": {"pw": "Maldarizzi2026", "nome": "MICHELE SCHIRALLI", "email": "m.schiralli@maldarizzi.com", "tel": "327 6810137", "ruolo": "interno"},
    "d.catanzaro": {"pw": "Maldarizzi2026", "nome": "DORIANA CATANZARO", "email": "d.catanzaro@maldarizzi.com", "tel": "349 756 8629", "ruolo": "interno"},
    "v.schiralli": {"pw": "Maldarizzi2026", "nome": "VINCENZO SCHIRALLI", "email": "v.schiralli@maldarizzi.com", "tel": "327 681 0137", "ruolo": "interno"},
    "a.lozito": {"pw": "Maldarizzi2026", "nome": "ALESSANDRA LOZITO", "email": "a.lozito@maldarizzi.com", "tel": "340 450 7513", "ruolo": "interno"},
    "p.nolli": {"pw": "Maldarizzi2026", "nome": "PASQUALE NOLLI", "email": "pasquale@omniaprima.com", "tel": "331 399 3389", "ruolo": "interno"},
    "admin": {"pw": "cipiacemigliorare", "nome": "ADMIN MALDARIZZI", "email": "admin@admin.com", "tel": "000 0000000", "ruolo": "admin"}
}

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["current_user"] = None

    if not st.session_state["authenticated"]:
        st.markdown("<style>.stApp { background-color: #000000; }</style>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if os.path.exists("logo.png"): st.image("logo.png", width=200)
            st.subheader("Portale Noleggio Maldarizzi")
            user = st.text_input("Username (es. a.corallo)").lower().strip()
            password = st.text_input("Password", type="password")
            if st.button("Accedi"):
                utente = DATABASE_UTENTI.get(user)
                if utente and password == utente.get("pw"):
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = utente
                    st.rerun()
                else: st.error("Credenziali errate o utente inesistente")
        return False
    return True

# --- INIZIALIZZAZIONE VARIABILI IN MEMORIA ---
if "pagina_attiva" not in st.session_state: st.session_state["pagina_attiva"] = "🔥 Offerte del Mese"
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
if "val_usa_gomme" not in st.session_state: st.session_state["val_usa_gomme"] = True
if "val_tipo_gomme" not in st.session_state: st.session_state["val_tipo_gomme"] = "ILLIMITATE"
if "val_note" not in st.session_state: st.session_state["val_note"] = ""
if "origine_preventivo" not in st.session_state: st.session_state["origine_preventivo"] = "Manuale"

# --- 2. CLASSE PDF FASCICOLO (LAYOUT GRIGLIA ORIZZONTALE) ---
class FascicoloPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4') # 'L' = Landscape (Orizzontale)
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(True, margin=15)
        if os.path.exists("Rubik-Light.ttf"): self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
        if os.path.exists("Rubik-Bold.ttf"): self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
        self.f_f = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

    def header(self):
        if os.path.exists("sfondo_nero.jpg"):
            try: self.image("sfondo_nero.jpg", 0, 0, 297, 210)
            except Exception: self.set_fill_color(20, 20, 20); self.rect(0, 0, 297, 210, 'F')
        else: self.set_fill_color(20, 20, 20); self.rect(0, 0, 297, 210, 'F')

        if os.path.exists("logo.png"):
            try: self.image("logo.png", 10, 10, 45) 
            except Exception: pass

# ==========================================
# AVVIO APP PRINCIPALE
# ==========================================
st.set_page_config(page_title="Portale Maldarizzi", layout="wide")
try: locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
except: pass

if check_password():
    utente_loggato = st.session_state["current_user"]
    nome_cons = utente_loggato["nome"]
    email_cons = utente_loggato["email"]
    tel_cons = utente_loggato["tel"]
    
    # --- MENU LATERALE ---
    if os.path.exists("logo.png"): st.sidebar.image("logo.png", width=180)
    st.sidebar.markdown(f"👤 Benvenuto, **{utente_loggato['nome']}**")
    st.sidebar.markdown(f"🏷️ Ruolo: *{utente_loggato['ruolo'].upper()}*")
    st.sidebar.markdown("---")
    
    if utente_loggato["ruolo"] == "admin":
        st.sidebar.markdown("### 📊 Pannello Direzione")
        if os.path.exists("statistiche_preventivi.csv"):
            df_stats = pd.read_csv("statistiche_preventivi.csv")
            st.sidebar.success(f"Totale Preventivi: **{len(df_stats)}**")
            with open("statistiche_preventivi.csv", "rb") as f:
                st.sidebar.download_button("📥 Scarica Statistiche", data=f, file_name="Statistiche.csv", mime="text/csv")
        st.sidebar.markdown("---")

    opzioni_menu = ["🔥 Offerte del Mese", "🎯 Preventivatore Strumentale"]
    try: idx_menu = opzioni_menu.index(st.session_state["pagina_attiva"])
    except: idx_menu = 0
    menu_scelta = st.sidebar.radio("📌 MENU PRINCIPALE", opzioni_menu, index=idx_menu)
    if menu_scelta != st.session_state["pagina_attiva"]:
        st.session_state["pagina_attiva"] = menu_scelta
        st.rerun()
        
    st.sidebar.markdown("---")
    
    # ==========================================
    # CARRELLO E STAMPA FASCICOLO (GRIGLIA) NEL MENU LATERALE
    # ==========================================
    if len(st.session_state["lista_preventivi"]) > 0:
        st.sidebar.info(f"🛒 **FASCICOLO PRONTO**\nHai **{len(st.session_state['lista_preventivi'])}** auto in lista.")
        
        # GENERAZIONE PDF FASCICOLO (GRIGLIA ORIZZONTALE)
        pdf_fascicolo = FascicoloPDF()
        pdf_fascicolo.add_page()
        
        # Titolo e Cliente
        pdf_fascicolo.set_y(35)
        pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 18)
        pdf_fascicolo.set_text_color(201, 188, 65)
        pdf_fascicolo.cell(0, 10, "FASCICOLO OFFERTE COMMERCIALI", align="C", ln=True)
        
        pdf_fascicolo.set_font(pdf_fascicolo.f_f, "", 12)
        pdf_fascicolo.set_text_color(255, 255, 255)
        cliente_nome = st.session_state.get("val_cliente", "Gentile Cliente").upper()
        pdf_fascicolo.cell(0, 8, f"Spett.le: {pulisci_testo(cliente_nome)}", align="C", ln=True)
        pdf_fascicolo.ln(10)

        # INTESTAZIONE TABELLA GRIGLIA
        pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 10)
        pdf_fascicolo.set_fill_color(50, 50, 50)
        pdf_fascicolo.set_text_color(201, 188, 65)
        
        w_vei, w_mesi, w_ant, w_can, w_serv = 70, 30, 25, 25, 127
        
        pdf_fascicolo.cell(w_vei, 10, " MARCA E MODELLO", border=1, fill=True)
        pdf_fascicolo.cell(w_mesi, 10, " MESI / KM", border=1, align="C", fill=True)
        pdf_fascicolo.cell(w_ant, 10, " ANTICIPO", border=1, align="C", fill=True)
        pdf_fascicolo.cell(w_can, 10, " CANONE", border=1, align="C", fill=True)
        pdf_fascicolo.cell(w_serv, 10, " SERVIZI INCLUSI", border=1, fill=True)
        pdf_fascicolo.ln()

        # RIGHE DELLA TABELLA
        pdf_fascicolo.set_text_color(255, 255, 255)
        for p in st.session_state["lista_preventivi"]:
            veicolo = f"{p['marca']} {p['versione']}"[:42]
            mesi_km = f"{p['durata']}m / {p['km']}km"
            anticipo = f"Euro {str(p['anticipo']).replace('.0','')}"
            canone = f"Euro {str(p['canone']).replace('.0','')}"
            
            serv_list = [f"RCA {p['p_rca']}", f"I/F {p['p_if']}", f"Kasko {p['p_kasko']}"]
            if p.get('g_num'): serv_list.append(f"Gomme {p['g_num']}")
            if p.get('vett_sost'): serv_list.append("Vett. Sost.")
            servizi = " | ".join(serv_list)[:90]

            pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 9)
            pdf_fascicolo.cell(w_vei, 10, f" {pulisci_testo(veicolo)}", border=1)
            
            pdf_fascicolo.set_font(pdf_fascicolo.f_f, "", 9)
            pdf_fascicolo.cell(w_mesi, 10, pulisci_testo(mesi_km), border=1, align="C")
            pdf_fascicolo.cell(w_ant, 10, pulisci_testo(anticipo), border=1, align="C")
            
            pdf_fascicolo.set_text_color(201, 188, 65)
            pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 10)
            pdf_fascicolo.cell(w_can, 10, pulisci_testo(canone), border=1, align="C")
            
            pdf_fascicolo.set_text_color(255, 255, 255)
            pdf_fascicolo.set_font(pdf_fascicolo.f_f, "", 8)
            pdf_fascicolo.cell(w_serv, 10, f" {pulisci_testo(servizi)}", border=1)
            pdf_fascicolo.ln()
            
        # PIE DI PAGINA
        pdf_fascicolo.ln(10)
        pdf_fascicolo.set_font(pdf_fascicolo.f_f, "I", 8)
        pdf_fascicolo.set_text_color(180, 180, 180)
        pdf_fascicolo.cell(0, 4, "*Canone non comprende tassa automobilistica. Validita' offerta: 30gg.", align="L", ln=True)
        pdf_fascicolo.set_text_color(255, 255, 255)
        pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 9)
        pdf_fascicolo.cell(0, 5, f"Consulente: {nome_cons.upper()} | Tel: {tel_cons} | E-mail: {email_cons}", align="L", ln=True)
        
        pdf_fascicolo.output("preventivo_fascicolo_sidebar.pdf")
        
        with open("preventivo_fascicolo_sidebar.pdf", "rb") as f:
            st.sidebar.download_button("📩 SCARICA FASCICOLO (GRIGLIA)", f, "Fascicolo_Offerte.pdf", "application/pdf")
            
        if st.sidebar.button("🗑️ Svuota Fascicolo"):
            st.session_state["lista_preventivi"] = []
            st.rerun()
        st.sidebar.markdown("---")
        
    if st.sidebar.button("🚪 Esci"):
        st.session_state["authenticated"] = False
        st.rerun()

    # ==========================================
    # SEZIONE 1: VETRINA CON DOPPIO DATABASE
    # ==========================================
    if st.session_state["pagina_attiva"] == "🔥 Offerte del Mese":
        st.title("🔥 Promozioni del Mese")
        st.markdown("Sfoglia le offerte. Puoi personalizzarle nel preventivatore o aggiungerle direttamente al Fascicolo!")
        
        with st.sidebar.expander("📥 CARICAMENTO DATABASE PROMO", expanded=False):
            file_promo = st.file_uploader("1. Database Generico", type=["xlsx", "csv"], key="file1")
            if file_promo:
                with open("promo_mese.xlsx", "wb") as f: f.write(file_promo.getbuffer())
                st.success("✅ DB Generico Aggiornato!")

            file_4v = st.file_uploader("2. File 4Vantage Ayvens", type=["xlsx", "csv"], key="file2")
            if file_4v:
                with open("promo_4vantage.csv", "wb") as f: f.write(file_4v.getbuffer())
                st.success("✅ DB 4Vantage Aggiornato!")

        # --- UNIONE DEI DUE DATABASE ---
        df_list = []
        if os.path.exists("promo_mese.xlsx"):
            try:
                df_main = leggi_file_dati("promo_mese.xlsx")
                df_main.columns = df_main.columns.str.strip().str.upper()
                df_list.append(df_main)
            except: pass

        if os.path.exists("promo_4vantage.csv"):
            try:
                df_4v = leggi_file_dati("promo_4vantage.csv")
                df_4v.columns = df_4v.columns.str.strip().str.upper()
                
                # Traduttore universale per le colonne del 4Vantage
                df_4v = df_4v.rename(columns={'MARCHIO': 'MARCA', 'KMS': 'KM TOTALI', 'COMMISSIONE': 'COMMISSIONI'})
                df_4v['OFFERTA'] = "4VANTAGE"
                if 'PLAYER' not in df_4v.columns: df_4v['PLAYER'] = "AYVENS"
                
                df_list.append(df_4v)
            except Exception as e:
                st.error(f"Errore caricamento 4Vantage: {str(e)}")

        if df_list:
            try:
                df_promo = pd.concat(df_list, ignore_index=True)
                df_promo = df_promo.fillna("") 
                
                c_search, c_alimen, c_player = st.columns([2, 1, 1])
                with c_search: 
                    ricerca = st.text_input("🔍 Cerca per marca o modello...").upper()
                with c_alimen:
                    if 'ALIMENTAZIONE' in df_promo.columns:
                        lista_alimen = ["Tutte"] + sorted([str(x).upper() for x in df_promo['ALIMENTAZIONE'].unique() if str(x).strip()])
                        filtro_alimen = st.selectbox("⚡ Alimentazione", lista_alimen)
                    else: 
                        filtro_alimen = "Tutte"
                with c_player:
                    if 'PLAYER' in df_promo.columns:
                        lista_player = ["Tutti"] + sorted([str(x).upper() for x in df_promo['PLAYER'].unique() if str(x).strip()])
                        filtro_player = st.selectbox("🏢 Noleggiatore", lista_player)
                    else:
                        filtro_player = "Tutti"
                
                st.markdown("---")
                offerte_filtrate = []
                for _, row in df_promo.iterrows():
                    marca = str(row.get('MARCA', '')).strip().upper()
                    modello = str(row.get('MODELLO', '')).strip()
                    alimen = str(row.get('ALIMENTAZIONE', '')).strip().upper() if 'ALIMENTAZIONE' in df_promo.columns else ""
                    offerta_tipo = str(row.get('OFFERTA', '')).strip()
                    player = str(row.get('PLAYER', '')).strip().upper()
                    commissioni = str(row.get('COMMISSIONI', '')).strip()
                    link_raw = str(row.get('LINK OFFERTA', '')).strip()
                    link_valido = link_raw if link_raw.startswith("http") else ("https://" + link_raw if link_raw.startswith("www") else "")
                    
                    try: canone = float(str(row.get('CANONE', 0)).replace(',','.'))
                    except: canone = 0.0
                    try: anticipo = float(str(row.get('ANTICIPO', 0)).replace(',','.'))
                    except: anticipo = 0.0
                    try: mesi = int(row.get('MESI', 0))
                    except: mesi = 0
                    try: km = int(float(str(row.get('KM TOTALI', 0)).replace(' ', '')))
                    except: km = 0

                    if ricerca and ricerca not in marca and ricerca not in modello.upper(): continue
                    if filtro_alimen != "Tutte" and alimen != filtro_alimen: continue
                    if filtro_player != "Tutti" and player != filtro_player: continue
                        
                    offerte_filtrate.append({
                        "marca": marca, "modello": modello, "canone": canone, 
                        "anticipo": anticipo, "durata": mesi, "km_totali": km,
                        "tipo": offerta_tipo, "player": player, "comm": commissioni, "link": link_valido
                    })
                
                # --- ORDINAMENTO CRESCENTE DEL CANONE ---
                offerte_filtrate = sorted(offerte_filtrate, key=lambda x: x['canone'])
                
                if not offerte_filtrate:
                    st.warning("Nessuna offerta trovata con questi parametri.")
                else:
                    colonne_griglia = st.columns(3)
                    for idx, auto in enumerate(offerte_filtrate):
                        with colonne_griglia[idx % 3]:
                            link_html = f'<a href="{auto["link"]}" target="_blank" style="color: #C9BC41; text-decoration: none; font-size: 13px;">🔗 Apri Offerta Web</a>' if auto["link"] else '<span style="color: #888; font-size: 12px;">Nessun link web</span>'
                            
                            st.markdown(f"""
                            <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px;">
                                <h3 style="margin-bottom: 0; color: #FFF;">{auto['marca']}</h3>
                                <h5 style="margin-top: 0; color: #AAA;">{auto['modello']}</h5>
                                <h1 style="color: #C9BC41; margin-bottom: 5px;">Euro {str(auto['canone']).replace('.0','')}<span style="font-size: 14px; color: #888;"> /mese</span></h1>
                                <p style="color: #DDD; font-size: 14px; margin-bottom: 10px;">
                                    ⏳ {auto['durata']} mesi | 🛣️ {auto['km_totali']} Km totali<br>
                                    💰 Anticipo: Euro {str(auto['anticipo']).replace('.0','')}
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
                            
                            c_btn1, c_btn2 = st.columns(2)
                            
                            # 1. TASTO PERSONALIZZA
                            with c_btn1:
                                if st.button(f"➡️ Personalizza", key=f"btn_pers_{idx}"):
                                    st.session_state["val_marca_stampa"] = auto['marca']
                                    st.session_state["val_versione_stampa"] = auto['modello']
                                    st.session_state["val_canone"] = float(auto['canone'])
                                    st.session_state["val_anticipo"] = float(auto['anticipo'])
                                    st.session_state["val_durata"] = auto['durata']
                                    st.session_state["val_input_mode"] = "Testo Libero"
                                    st.session_state["origine_preventivo"] = "Vetrina Promo" 
                                    
                                    dur = auto['durata']
                                    st.session_state["val_km"] = int((auto['km_totali'] / dur) * 12) if dur > 0 else auto['km_totali']
                                    
                                    p_upper = auto['player'].upper()
                                    t_upper = auto['tipo'].upper()
                                    st.session_state["val_p_rca"] = "250 Euro"
                                    st.session_state["val_p_kasko"] = "500 Euro"
                                    st.session_state["val_usa_gomme"] = False
                                    st.session_state["val_tipo_gomme"] = "ILLIMITATE"

                                    if "AYVENS" in p_upper:
                                        if "4VANTAGE" in t_upper or "4 VANTAGE" in t_upper:
                                            st.session_state["val_p_if"] = "0%"
                                            st.session_state["val_usa_gomme"] = True
                                            st.session_state["val_tipo_gomme"] = "INVERNALI"
                                        else: st.session_state["val_p_if"] = "500 Euro"
                                    elif "ARVAL" in p_upper: st.session_state["val_p_if"] = "500 Euro"
                                    elif "LEASYS" in p_upper or "SANTANDER" in p_upper or "ALPHABET" in p_upper: st.session_state["val_p_if"] = "10%"
                                    else: st.session_state["val_p_if"] = "10%"

                                    st.session_state["pagina_attiva"] = "🎯 Preventivatore Strumentale"
                                    st.rerun()
                                    
                            # 2. TASTO AGGIUNGI AL FASCICOLO RAPIDO
                            with c_btn2:
                                if st.button(f"➕ Fascicolo", key=f"btn_fasc_{idx}"):
                                    with st.spinner("Aggiunta al fascicolo..."):
                                        dur = auto['durata']
                                        km_anno = int((auto['km_totali'] / dur) * 12) if dur > 0 else auto['km_totali']
                                        
                                        p_upper = auto['player'].upper()
                                        t_upper = auto['tipo'].upper()
                                        p_if_val = "10%"
                                        gomme_val = None
                                        
                                        if "AYVENS" in p_upper:
                                            if "4VANTAGE" in t_upper or "4 VANTAGE" in t_upper:
                                                p_if_val = "0%"
                                                gomme_val = "INVERNALI"
                                            else: p_if_val = "500 Euro"
                                        elif "ARVAL" in p_upper: p_if_val = "500 Euro"
                                        elif "LEASYS" in p_upper or "SANTANDER" in p_upper or "ALPHABET" in p_upper: p_if_val = "10%"
                                        
                                        foto_bytes_api = scarica_foto_auto_api(auto['marca'], auto['modello'])
                                        
                                        auto_aggiunta = {
                                            "cliente": st.session_state.get("val_cliente", "Gentile CLIENTE"),
                                            "consegna": "IN SEDE MALDARIZZI", 
                                            "t_veicolo": "Nuovo", 
                                            "note": "", "opt": "", 
                                            "marca": pulisci_testo(auto['marca']), 
                                            "versione": pulisci_testo(auto['modello']), 
                                            "foto_bytes": foto_bytes_api, 
                                            "p_rca": "250 Euro", "p_if": p_if_val, "p_kasko": "500 Euro", 
                                            "infort": True, "g_num": gomme_val,
                                            "vett_sost": None, "canone": float(auto['canone']), 
                                            "anticipo": float(auto['anticipo']), "durata": dur, 
                                            "km": km_anno, "iva_text": "Iva Esclusa", 
                                            "origine_dati": "Fascicolo Rapido" 
                                        }
                                        st.session_state["lista_preventivi"].append(auto_aggiunta)
                                        st.success(f"✅ {auto['marca']} aggiunta al Fascicolo!")
                                        st.rerun() 

            except Exception as e:
                st.error(f"Errore caricamento database: {str(e)}")
        else:
            st.info("👈 Apri il menù 'CARICAMENTO DATABASE PROMO' nel menù laterale per inserire i file.")


    # ==========================================
    # SEZIONE 2: PREVENTIVATORE STRUMENTALE
    # ==========================================
    elif st.session_state["pagina_attiva"] == "🎯 Preventivatore Strumentale":
        st.title("🎯 Preventivatore Strumentale")
        
        st.sidebar.header("📥 Importa PDF Portale")
        pdf_portale = st.sidebar.file_uploader("Carica PDF (Arval, Leasys, Ayvens)", type=["pdf"])
        if pdf_portale and st.sidebar.button("🧠 Analizza e Compila Dati dal PDF"):
            try:
                pdf_bytes = io.BytesIO(pdf_portale.getvalue())
                reader = pypdf.PdfReader(pdf_bytes)
                testo_flat = re.sub(r'\s+', ' ', "".join([p.extract_text() for p in reader.pages])).strip()
                testo_upper = testo_flat.upper()
                st.session_state["val_input_mode"] = "Testo Libero"
                st.session_state["origine_preventivo"] = "Importazione da PDF"
                
                st.session_state["val_tipo_cliente"] = "Privato" if "IVA INCLUSA" in testo_upper or "C.F." in testo_upper or "PRIVATO" in testo_upper else "Partita IVA"
                brands = ['FIAT', 'CITROEN', 'FORD', 'AUDI', 'BMW', 'MERCEDES', 'VOLKSWAGEN', 'PEUGEOT', 'RENAULT', 'OPEL', 'ALFA ROMEO', 'JEEP', 'TOYOTA', 'NISSAN', 'VOLVO', 'KIA', 'HYUNDAI', 'DACIA', 'LANCIA', 'SEAT', 'CUPRA', 'SUZUKI', 'MAZDA', 'LAND ROVER', 'PORSCHE', 'TESLA', 'MINI', 'LEXUS', 'MASERATI', 'SMART', 'SKODA', 'HONDA', 'MG', 'DS', 'IVECO']

                if "AYVENS" in testo_upper or "SOCIETE GENERALE" in testo_upper or "ALD AUTOMOTIVE" in testo_upper:
                    m_cli = re.search(r':\s*([A-Za-z\s\,\'\.\-]+?)\s*\d{6,9}/\d{2,3}', testo_flat)
                    if m_cli: st.session_state["val_cliente"] = m_cli.group(1).split(",")[0].strip().upper()
                    m_vei = re.search(r'Veicolo:\s*(.*?)\s*Codici:', testo_flat, re.IGNORECASE) or re.search(r'Venduto\s+.*?(.*?)\s+\d{2}/\d{2}/\d{4}', testo_flat, re.IGNORECASE)
                    if m_vei:
                        vei = m_vei.group(1).strip()
                        st.session_state["val_versione_stampa"] = vei
                        st.session_state["val_marca_stampa"] = next((b for b in brands if vei.upper().startswith(b)), vei.split()[0].upper())
                    m_dur_km = re.search(r'\b(24|36|48|60)\s+(\d{4,7})\s+€', testo_flat)
                    if m_dur_km:
                        st.session_state["val_durata"] = int(m_dur_km.group(1))
                        st.session_state["val_km"] = int((int(m_dur_km.group(2)) / st.session_state["val_durata"]) * 12) if st.session_state["val_durata"]>0 else 0
                    m_can = re.findall(r'€\s*(\d{2,4}[,.]\d{2})', testo_flat)
                    if m_can: st.session_state["val_canone"] = sorted([float(c.replace(',', '.')) for c in m_can], reverse=True)[0]
                    m_ant = re.search(r'Anticipo\s*\(iva\s*esclusa\)\s*€\s*(\d{1,6}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_ant: st.session_state["val_anticipo"] = float(m_ant.group(1).replace(',', '.'))

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
                    if m_km: st.session_state["val_km"] = int((int(m_km.group(1).replace(' ', '')) / st.session_state["val_durata"]) * 12) if st.session_state.get("val_durata",0)>0 else 0
                    m_can = re.search(r'Canone Totale\s+€\s*(\d{1,4}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_can: st.session_state["val_canone"] = float(m_can.group(1).replace(',', '.'))
                    m_ant = re.search(r'Anticipo\s*€\s*([\d\s]+[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_ant: st.session_state["val_anticipo"] = float(m_ant.group(1).replace(' ', '').replace(',', '.'))

                elif "ARVAL" in testo_upper:
                    m_cli = re.search(r'Ragione Sociale\s+([A-Za-z0-9\s\&\.\'\-]+?)\s+(?:CF Cliente|C\.F\.|Codice|P\.?IVA)', testo_flat, re.IGNORECASE)
                    if m_cli: st.session_state["val_cliente"] = m_cli.group(1).strip().upper()
                    m_vei = re.search(r'per il veicolo\s+(.*?)\s+Canone', testo_flat, re.IGNORECASE)
                    if m_vei:
                        vei = m_vei.group(1).strip()
                        st.session_state["val_versione_stampa"] = vei
                        st.session_state["val_marca_stampa"] = next((b for b in brands if vei.upper().startswith(b)), vei.split()[0].upper())
                    m_can = re.search(r'Canone\s+(\d{1,4}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_can: st.session_state["val_canone"] = float(m_can.group(1).replace(',', '.'))
                    m_dur = re.search(r'durata\s+(\d{2,3})\s*mesi', testo_flat, re.IGNORECASE)
                    if m_dur: st.session_state["val_durata"] = int(m_dur.group(1))
                    m_km = re.search(r'km totali\s+(\d{2,6})', testo_flat, re.IGNORECASE)
                    if m_km: st.session_state["val_km"] = int((int(m_km.group(1)) / st.session_state.get("val_durata", 36)) * 12)
                    m_ant = re.search(r'Anticipo\s*(?:€|Euro)?\s*(\d{1,6}[,.]\d{2})', testo_flat, re.IGNORECASE)
                    if m_ant: st.session_state["val_anticipo"] = float(m_ant.group(1).replace(',', '.'))

                st.sidebar.success("✅ Dati estratti chirurgicamente!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Errore analisi PDF: {str(e)}")

        st.sidebar.markdown("---")
        uploaded_excel = st.sidebar.file_uploader("Aggiorna Listino (Excel)", type=["xlsx"])
        if uploaded_excel:
            with open("dati.xlsx", "wb") as f: f.write(uploaded_excel.getbuffer())
            st.sidebar.success("Database Listino aggiornato!")

        if os.path.exists("dati.xlsx"):
            excel = pd.ExcelFile("dati.xlsx")
            foglio = st.sidebar.selectbox("Seleziona Categoria Listino", excel.sheet_names)
            df = pd.read_excel("dati.xlsx", sheet_name=foglio, dtype=str)
        else:
            st.sidebar.warning("Carica dati.xlsx per ricerca da listino")
        
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
            usa_vett_sost = st.checkbox("Vettura Sostitutiva?", value=False)
            vett_sost_cat = st.selectbox("Categoria Sostitutiva", ["ECONOMY", "FAMILY SMALL", "FAMILY LARGE", "EXECUTIVE", "LUXURY"]) if usa_vett_sost else None
        
        with s3:
            usa_gomme = st.checkbox("Includere Pneumatici?", value=st.session_state.get("val_usa_gomme", True))
            g_num = "ILLIMITATE"
            if usa_gomme:
                opzioni_gomme = ["ILLIMITATE", "A NUMERO", "INVERNALI"]
                idx_gomme = opzioni_gomme.index(st.session_state.get("val_tipo_gomme", "ILLIMITATE")) if st.session_state.get("val_tipo_gomme", "ILLIMITATE") in opzioni_gomme else 0
                g_tipo = st.radio("Tipo Gomme", opzioni_gomme, horizontal=True, index=idx_gomme)
                
                if g_tipo == "A NUMERO":
                    g_num = st.number_input("N. Gomme", value=4, min_value=1)
                elif g_tipo == "INVERNALI":
                    g_num = "INVERNALI"
            else: 
                g_num = None

        st.markdown("---")
        st.subheader("💸 Dati Economici")
        n1, n2, n3, n4 = st.columns(4)
        iva_text = "Iva Inclusa" if tipo_cliente == "Privato" else "Iva Esclusa"
        with n1: canone = st.number_input(f"Canone ({iva_text})", value=float(st.session_state["val_canone"]))
        with n2: anticipo = st.number_input(f"Anticipo ({iva_text})", value=float(st.session_state["val_anticipo"]))
        with n3: 
            durate_disp = [24, 36, 48, 60]
            val_durata = int(st.session_state.get("val_durata", 36))
            if val_durata not in durate_disp: durate_disp.append(val_durata)
            durata = st.selectbox("Durata", sorted(durate_disp), index=sorted(durate_disp).index(val_durata))
        with n4: km = st.number_input("Km/Anno", value=int(st.session_state["val_km"]))

        st.markdown("---")
        
        if st.button("➕ AGGIUNGI AL FASCICOLO"):
            foto_bytes = foto_m.getvalue() if foto_m else None
            if not foto_bytes:
                with st.spinner('Ricerca immagine in corso...'):
                    foto_bytes_api = scarica_foto_auto_api(marca_stampa, versione_stampa)
                    if foto_bytes_api: foto_bytes = foto_bytes_api
            
            auto_aggiunta = {
                "cliente": pulisci_testo(nome_cliente), "consegna": pulisci_testo(consegna), 
                "t_veicolo": pulisci_testo(t_veicolo), "note": pulisci_testo(note_p), "opt": pulisci_testo(opt_p), 
                "marca": pulisci_testo(marca_stampa), "versione": pulisci_testo(versione_stampa), 
                "foto_bytes": foto_bytes, "p_rca": pulisci_testo(p_rca), "p_if": pulisci_testo(p_if), 
                "p_kasko": pulisci_testo(p_kasko), "infort": infort, "g_num": pulisci_testo(g_num) if g_num else None,
                "vett_sost": pulisci_testo(vett_sost_cat), "canone": canone, "anticipo": anticipo, "durata": durata, 
                "km": km, "iva_text": iva_text, "origine_dati": st.session_state.get("origine_preventivo", "Manuale") 
            }
            st.session_state["lista_preventivi"].append(auto_aggiunta)
            st.success(f"✅ Veicolo aggiunto! Puoi stampare la griglia dal menù laterale a sinistra.")
            st.rerun() # Aggiorna la pagina per mostrare il bottone di stampa subito
