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
import random

# --- CREAZIONE CARTELLA CACHE PER RISPARMIARE CHIAMATE FOTO ---
if not os.path.exists("Foto_Cache"):
    os.makedirs("Foto_Cache")

# --- HELPER LETTURA FILE ---
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

# --- FUNZIONE EFFETTO BANANE ---
def show_bananas():
    bananas_html = """
    <style>
    @keyframes banana-fall { 
        0% {top: -10%; opacity: 1; transform: rotate(0deg);} 
        100% {top: 100%; opacity: 0; transform: rotate(360deg);} 
    } 
    .banana {
        position: fixed; 
        font-size: 2.5rem; 
        z-index: 9999; 
        animation: banana-fall linear forwards;
    }
    </style>
    """
    for _ in range(40):
        left = random.randint(0, 100)
        delay = random.uniform(0, 2.5)
        duration = random.uniform(2.5, 4.5)
        bananas_html += f"<div class='banana' style='left: {left}%; animation-duration: {duration}s; animation-delay: {delay}s;'>🍌</div>"
    st.markdown(bananas_html, unsafe_allow_html=True)

# --- NUOVA FUNZIONE: RECUPERO FOTO DA GOOGLE IMMAGINI ---
def scarica_foto_auto_api(marca, versione):
    # ⚠️ INSERISCI QUI I TUOI DATI GOOGLE:
    GOOGLE_API_KEY = "AIzaSyDuv1SOc8kLh9eqYo_dh9kQg9MiCQl3-dI"
    GOOGLE_CX = "419da089f0736400f"
    
    if GOOGLE_API_KEY == "inserisci qui la tua chiave api":
        st.warning("⚠️ Diagnostica: Inserisci le chiavi di Google nel codice.")
        return None

    marca_clean = str(marca).strip().title()
    parti_versione = str(versione).strip().split()
    modello_clean = parti_versione[0].title() if parti_versione else ""
    trim_clean = " ".join(parti_versione[1:]).title() if len(parti_versione) > 1 else ""
    
    nome_file_cache = f"Foto_Cache/{marca_clean}_{modello_clean}_{trim_clean}.jpg".replace(" ", "_").replace("/", "_").lower()
    
    if os.path.exists(nome_file_cache):
        with open(nome_file_cache, "rb") as f:
            st.toast(f"⚡ Foto recuperata dalla Memoria Interna! (Costo: 0)")
            return f.read()

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
                                with open(nome_file_cache, "wb") as f:
                                    f.write(risposta_foto.content)
                                st.success("✅ FOTO GOOGLE: Scaricata e salvata in Memoria!")
                                return risposta_foto.content
                        except: continue
                st.error("❌ I link trovati da Google non erano immagini scaricabili.")
            else:
                st.warning(f"⚠️ Google non ha trovato immagini per questa ricerca.")
        else:
            st.error(f"❌ Errore Google API: {risposta.json().get('error', {}).get('message', 'Errore Sconosciuto')}")
    except Exception as e:
        st.error(f"❌ Errore di rete: {e}")
        
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
    "v.miccoli": {"pw": "Maldarizzi2026", "nome": "VINCENZO MICCOLI", "email": "v.miccoli@maldarizzi.com", "tel": "3357403250", "ruolo": "interno"},
    "a.lozito": {"pw": "Maldarizzi2026", "nome": "ALESSANDRA LOZITO", "email": "a.lozito@maldarizzi.com", "tel": "340 450 7513", "ruolo": "interno"},
    "p.nolli": {"pw": "Maldarizzi2026", "nome": "PASQUALE NOLLI", "email": "pasquale@omniaprima.com", "tel": "331 399 3389", "ruolo": "interno"},
    "admin": {"pw": "cipiacemigliorare", "nome": "ADMIN MALDARIZZI", "email": "admin@admin.com", "tel": "000 0000000", "ruolo": "admin"}
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
            user = st.text_input("Username (es. a.corallo)").lower().strip()
            password = st.text_input("Password", type="password")
            if st.button("Accedi"):
                utente = DATABASE_UTENTI.get(user)
                if utente and password == utente.get("pw"):
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = utente
                    st.rerun()
                else:
                    st.error("Credenziali errate o utente inesistente")
        return False
    return True

# --- INIZIALIZZAZIONE VARIABILI IN MEMORIA ---
if "pagina_attiva" not in st.session_state: st.session_state["pagina_attiva"] = "🔥 Offerte del Mese"

if "lista_preventivi" not in st.session_state: st.session_state["lista_preventivi"] = []
if "lista_fascicolo" not in st.session_state: st.session_state["lista_fascicolo"] = [] 
if "pdf_carrello_pronto" not in st.session_state: st.session_state["pdf_carrello_pronto"] = False

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
if "val_usa_gomme" not in st.session_state: st.session_state["val_usa_gomme"] = False
if "val_tipo_gomme" not in st.session_state: st.session_state["val_tipo_gomme"] = "ILLIMITATE"
if "val_n_gomme" not in st.session_state: st.session_state["val_n_gomme"] = 4
if "val_stagione_gomme" not in st.session_state: st.session_state["val_stagione_gomme"] = "Estive"
if "debug_text" not in st.session_state: st.session_state["debug_text"] = ""
if "val_note" not in st.session_state: st.session_state["val_note"] = ""
if "origine_preventivo" not in st.session_state: st.session_state["origine_preventivo"] = "Manuale"

# --- 2. CLASSE PDF PREVENTIVATORE (VERTICALE) ---
class MaldarizziPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
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

# --- 3. NUOVA CLASSE PDF CARRELLO (ORIZZONTALE) ---
class FascicoloPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4') # L = Orizzontale
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(True, margin=15)
        if os.path.exists("Rubik-Light.ttf"):
            self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
        if os.path.exists("Rubik-Bold.ttf"):
            self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
        self.f_f = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

    def header(self):
        # Punta al nuovo sfondo per la griglia orizzontale
        if os.path.exists("sfondo nero orizz.jpg"):
            try:
                self.image("sfondo nero orizz.jpg", 0, 0, 297, 210)
            except Exception:
                self.set_fill_color(20, 20, 20)
                self.rect(0, 0, 297, 210, 'F')
        elif os.path.exists("sfondo_nero.jpg"):
            try:
                self.image("sfondo_nero.jpg", 0, 0, 297, 210)
            except Exception:
                self.set_fill_color(20, 20, 20)
                self.rect(0, 0, 297, 210, 'F')
        else:
            self.set_fill_color(20, 20, 20)
            self.rect(0, 0, 297, 210, 'F')

        if os.path.exists("logo.png"):
            try:
                self.image("logo.png", 10, 10, 45) 
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
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", width=180)
        
    st.sidebar.markdown(f"👤 Benvenuto, **{utente_loggato['nome']}**")
    st.sidebar.markdown(f"🏷️ Ruolo: *{utente_loggato['ruolo'].upper()}*")
    st.sidebar.markdown("---")
    
    if utente_loggato["ruolo"] == "admin":
        st.sidebar.markdown("### 📊 Pannello Direzione")
        if os.path.exists("statistiche_preventivi.csv"):
            df_stats = pd.read_csv("statistiche_preventivi.csv")
            totale_prev = len(df_stats)
            st.sidebar.success(f"Totale Preventivi Generati: **{totale_prev}**")
            with open("statistiche_preventivi.csv", "rb") as f:
                st.sidebar.download_button("📥 Scarica Excel Statistiche", data=f, file_name="Statistiche_Maldarizzi.csv", mime="text/csv")
        else:
            st.sidebar.warning("Nessun preventivo registrato finora.")
        st.sidebar.markdown("---")

    opzioni_menu = ["🔥 Offerte del Mese", "🎯 Preventivatore Strumentale"]
    try: idx_menu = opzioni_menu.index(st.session_state["pagina_attiva"])
    except: idx_menu = 0
    menu_scelta = st.sidebar.radio("📌 MENU PRINCIPALE", opzioni_menu, index=idx_menu)
    if menu_scelta != st.session_state["pagina_attiva"]:
        st.session_state["pagina_attiva"] = menu_scelta
        st.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Esci"):
        st.session_state["authenticated"] = False
        st.rerun()

    # ==========================================
    # SEZIONE 1: VETRINA PROMO E CARRELLO GRIGLIA
    # ==========================================
    if st.session_state["pagina_attiva"] == "🔥 Offerte del Mese":
        
        # --- UI DEL CARRELLO PROMO (IN ALTO) ---
        if len(st.session_state["lista_fascicolo"]) > 0:
            st.info(f"🛒 **CARRELLO OFFERTE:** Hai {len(st.session_state['lista_fascicolo'])} promozioni selezionate.")
            col_cart1, col_cart2, col_cart3 = st.columns([2, 1, 1])
            with col_cart1:
                cliente_carrello = st.text_input("👤 Intesta queste offerte a (Nome Cliente):", value=st.session_state.get("val_cliente", "Gentile CLIENTE"))
                st.session_state["val_cliente"] = cliente_carrello
            
            with col_cart2:
                st.write("") 
                st.write("")
                if st.button("🚀 GENERA STAMPA CARRELLO"):
                    pdf_fascicolo = FascicoloPDF()
                    pdf_fascicolo.add_page()
                    
                    pdf_fascicolo.set_y(35)
                    pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 18)
                    pdf_fascicolo.set_text_color(201, 188, 65)
                    pdf_fascicolo.cell(0, 10, "FASCICOLO OFFERTE COMMERCIALI", align="C", ln=True)
                    
                    pdf_fascicolo.set_font(pdf_fascicolo.f_f, "", 12)
                    pdf_fascicolo.set_text_color(255, 255, 255)
                    pdf_fascicolo.cell(0, 8, f"Spett.le: {pulisci_testo(st.session_state['val_cliente'].upper())}", align="C", ln=True)
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
                    pdf_fascicolo.cell(w_serv, 10, " PENALI E SERVIZI INCLUSI", border=1, fill=True)
                    pdf_fascicolo.ln()

                    # RIGHE
                    pdf_fascicolo.set_text_color(255, 255, 255)
                    for p in st.session_state["lista_fascicolo"]:
                        
                        # Logica di calcolo servizi in base al Player salvato nel carrello
                        p_upper = str(p['player']).upper()
                        t_upper = str(p['tipo']).upper()
                        p_if_val = "10%"
                        gomme_str = ""
                        
                        if "AYVENS" in p_upper:
                            if "4VANTAGE" in t_upper or "4 VANTAGE" in t_upper:
                                p_if_val = "0%"
                                gomme_str = " | Gomme Invernali"
                            else: p_if_val = "500 Euro"
                        elif "ARVAL" in p_upper: p_if_val = "500 Euro"
                        elif "LEASYS" in p_upper or "SANTANDER" in p_upper or "ALPHABET" in p_upper: p_if_val = "10%"
                        else: p_if_val = "10%"

                        servizi = f"RCA 250 Euro | I/F {p_if_val} | Kasko 500 Euro | Manutenzione | Soccorso{gomme_str}"
                        
                        veicolo = f"{p['marca']} {p['modello']}"[:42]
                        mesi_km = f"{p['durata']}m / {p['km']}km"
                        anticipo = f"Euro {str(p['anticipo']).replace('.0','')}"
                        canone = f"Euro {str(p['canone']).replace('.0','')}"

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

                    pdf_fascicolo.ln(10)
                    pdf_fascicolo.set_font(pdf_fascicolo.f_f, "I", 8)
                    pdf_fascicolo.set_text_color(180, 180, 180)
                    pdf_fascicolo.cell(0, 4, "*Canone non comprende tassa automobilistica. Validita' offerta: 30gg.", align="L", ln=True)
                    pdf_fascicolo.set_text_color(255, 255, 255)
                    pdf_fascicolo.set_font(pdf_fascicolo.f_f, "B", 9)
                    pdf_fascicolo.cell(0, 5, f"Consulente: {nome_cons.upper()} | Tel: {tel_cons} | E-mail: {email_cons}", align="L", ln=True)
                    
                    pdf_fascicolo.output("Fascicolo_Offerte.pdf")
                    st.session_state["pdf_carrello_pronto"] = True

            with col_cart3:
                st.write("")
                st.write("")
                if st.button("🗑️ Svuota Carrello"):
                    st.session_state["lista_fascicolo"] = []
                    st.session_state["pdf_carrello_pronto"] = False
                    st.rerun()
            
            # MOSTRA TASTO DOWNLOAD E BANANE 🍌
            if st.session_state.get("pdf_carrello_pronto"):
                show_bananas()
                with open("Fascicolo_Offerte.pdf", "rb") as f:
                    st.download_button("📩 IL PDF E' PRONTO: SCARICA ORA!", f, "Fascicolo_Offerte.pdf", "application/pdf")
                    
            st.markdown("---")

        st.title("🔥 Promozioni del Mese")
        st.markdown("Sfoglia le offerte, verifica i dettagli e trasferiscile nel preventivatore con un clic.")
        
        # --- CARICAMENTO DATABASE (ANCHE 4VANTAGE) ---
        with st.sidebar.expander("📥 CARICAMENTO DATABASE PROMO", expanded=False):
            file_promo = st.file_uploader("1. Database Generico", type=["xlsx", "csv"], key="file1")
            if file_promo:
                with open("promo_mese.xlsx", "wb") as f: f.write(file_promo.getbuffer())
                st.success("✅ DB Generico Aggiornato!")

            file_4v = st.file_uploader("2. File 4Vantage Ayvens", type=["xlsx", "csv"], key="file2")
            if file_4v:
                with open("promo_4vantage.csv", "wb") as f: f.write(file_4v.getbuffer())
                st.success("✅ DB 4Vantage Aggiornato!")

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
                # Traduttore Universale
                df_4v = df_4v.rename(columns={'MARCHIO': 'MARCA', 'KMS': 'KM TOTALI', 'KMS ': 'KM TOTALI', 'FUEL': 'ALIMENTAZIONE', 'COMMISSIONE': 'COMMISSIONI', 'COMMISSIONE ': 'COMMISSIONI'})
                df_4v['OFFERTA'] = "4VANTAGE"
                if 'PLAYER' not in df_4v.columns: df_4v['PLAYER'] = "AYVENS"
                df_list.append(df_4v)
            except Exception as e:
                st.error(f"Errore 4Vantage: {str(e)}")

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
                    link_raw = str(row.get('LINK OFFERTA', '')).strip() if 'LINK OFFERTA' in df_promo.columns else str(row.get('link offerta', '')).strip()
                    link_valido = link_raw if link_raw.startswith("http") else ("https://" + link_raw if link_raw.startswith("www") else "")
                    
                    try: canone = float(str(row.get('CANONE', 0)).replace(' ', '').replace(',','.'))
                    except: canone = 0.0
                    try: anticipo = float(str(row.get('ANTICIPO', 0)).replace(' ', '').replace(',','.'))
                    except: anticipo = 0.0
                    try: mesi = int(row.get('MESI', 0))
                    except: mesi = 0
                    try: km = int(float(str(row.get('KM TOTALI', 0)).replace(' ', '').replace(',','.')))
                    except: km = 0

                    if ricerca and ricerca not in marca and ricerca not in modello.upper(): continue
                    if filtro_alimen != "Tutte" and alimen != filtro_alimen: continue
                    if filtro_player != "Tutti" and player != filtro_player: continue
                        
                    offerte_filtrate.append({
                        "marca": marca, "modello": modello, "canone": canone, 
                        "anticipo": anticipo, "durata": mesi, "km": km,
                        "tipo": offerta_tipo, "player": player, "comm": commissioni, "link": link_valido
                    })
                
                # Ordinamento per canone più basso
                offerte_filtrate = sorted(offerte_filtrate, key=lambda x: x['canone'])

                if not offerte_filtrate:
                    st.warning("Nessuna offerta trovata con questi parametri.")
                else:
                    colonne_griglia = st.columns(3)
                    for idx, auto in enumerate(offerte_filtrate):
                        with colonne_griglia[idx % 3]:
                            link_html = f'<a href="{auto["link"]}" target="_blank" style="color: #C9BC41;">🔗 Apri Offerta Web</a>' if auto["link"] else '<span style="color: #888;">Nessun link web</span>'
                            
                            st.markdown(f"""
                            <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px;">
                                <h3 style="margin-bottom: 0; color: #FFF;">{auto['marca']}</h3>
                                <h5 style="margin-top: 0; color: #AAA;">{auto['modello']}</h5>
                                <h1 style="color: #C9BC41; margin-bottom: 5px;">Euro {str(auto['canone']).replace('.0','')} <span style="font-size: 14px; color: #888;"> /mese</span></h1>
                                <p style="color: #DDD; font-size: 14px; margin-bottom: 10px;">
                                    ⏳ {auto['durata']} mesi | 🛣️ {auto['km']} Km totali<br>
                                    💰 Anticipo: Euro {str(auto['anticipo']).replace('.0','')}
                                </p>
                                <hr style="border-top: 1px solid #444; margin: 10px 0;">
                                <p style="font-size: 13px; color: #BBB;">🏢 Player: {auto['player']}<br>🏷️ Tipo: {auto['tipo']}<br>💶 Comm: {auto['comm']}</p>
                                {link_html}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_btn1, c_btn2 = st.columns(2)
                            
                            with c_btn1:
                                if st.button("➡️ Utilizza la Promo", key=f"btn_promo_{idx}"):
                                    st.session_state["val_marca_stampa"] = auto['marca']
                                    st.session_state["val_versione_stampa"] = auto['modello']
                                    st.session_state["val_canone"] = float(auto['canone'])
                                    st.session_state["val_anticipo"] = float(auto['anticipo'])
                                    st.session_state["val_durata"] = auto['durata']
                                    
                                    # Divisione per i Km Annuali
                                    dur = auto['durata']
                                    st.session_state["val_km"] = int((auto['km'] / dur) * 12) if dur > 0 else auto['km']
                                    
                                    st.session_state["val_input_mode"] = "Testo Libero"
                                    st.session_state["origine_preventivo"] = "Vetrina Promo" 
                                    
                                    p_upper = auto['player'].upper()
                                    t_upper
