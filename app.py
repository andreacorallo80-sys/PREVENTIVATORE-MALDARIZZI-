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
            df = pd.read_csv(percorso, sep=";", on_bad_lines='skip')
            if len(df.columns) < 3: 
                df = pd.read_csv(percorso, sep=",", on_bad_lines='skip')
            return df
        except:
            df = pd.read_csv(percorso, sep=";", encoding="latin-1", on_bad_lines='skip')
            if len(df.columns) < 3: 
                df = pd.read_csv(percorso, sep=",", encoding="latin-1", on_bad_lines='skip')
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

# --- NUOVA FUNZIONE: RECUPERO FOTO IMAGIN.STUDIO (ANTI-TELO ROSSO POTENZIATO) ---
def scarica_foto_auto_api(marca, versione):
    # 1. Pulizia Marca
    marca_clean = str(marca).strip().lower().replace(" ", "")
    
    # Fix specifici per marchi composti che Imagin.studio vuole col trattino
    if marca_clean == "alfaromeo": marca_clean = "alfa-romeo"
    if marca_clean == "landrover": marca_clean = "land-rover"
    
    # 2. Pulizia Modello Estrema
    versione_lower = str(versione).strip().lower()
    parti_versione = versione_lower.split()
    
    if not parti_versione:
        return None
        
    modello_clean = parti_versione[0]
    
    # Gestione modelli a due parole
    if len(parti_versione) > 1:
        seconda_parola = parti_versione[1]
        if seconda_parola in ["cross", "aircross", "x", "l", "sport", "e", "rover", "countryman"]:
            modello_clean = f"{parti_versione[0]}{seconda_parola}"
            
    # Fix specifici per l'Italia
    if modello_clean == "500e": modello_clean = "500"
    if modello_clean == "pandina": modello_clean = "panda"
    
    nome_file_cache = f"Foto_Cache/{marca_clean}_{modello_clean}.png".replace("/", "_")
    
    # 1. Controllo Cache con AUTOPULIZIA del telo rosso
    if os.path.exists(nome_file_cache):
        with open(nome_file_cache, "rb") as f:
            dati_foto = f.read()
            # Se la foto in memoria pesa meno di 40KB, è un telo rosso salvato per sbaglio! Lo distruggiamo.
            if len(dati_foto) > 40000:
                st.toast(f"⚡ Foto di {marca.title()} recuperata dalla Memoria!")
                return dati_foto
            
        # Se era un telo rosso, eliminalo dalla cache
        os.remove(nome_file_cache)

    url_api = f"https://cdn.imagin.studio/getImage?customer=demo&make={marca_clean}&modelFamily={modello_clean}&angle=23&paintId=pspc0004&zoomType=fullscreen"
    
    try:
        headers_browser = {"User-Agent": "Mozilla/5.0"}
        risposta_foto = requests.get(url_api, headers=headers_browser, timeout=10)
        
        if risposta_foto.status_code == 200 and "image" in risposta_foto.headers.get("Content-Type", ""):
            
            # SCUDO ANTI-TELO FINALE: Scarta tutto ciò che è sotto i 40KB
            if len(risposta_foto.content) < 40000:
                st.warning(f"⚠️ Imagin.studio non ha il render esatto per {marca.title()} {modello_clean.title()} (Immagine generica scartata).")
                import time
                time.sleep(2)
                return None
                
            with open(nome_file_cache, "wb") as f:
                f.write(risposta_foto.content)
            st.success(f"✅ FOTO EUROPEA: {marca.title()} {modello_clean.title()} trovata e scontornata!")
            return risposta_foto.content
            
    except Exception as e:
        st.error(f"❌ Errore API Imagin.studio: {e}")
        
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

# --- INIZIALIZZAZIONE VARIABILI E SCUDO ANTI-CRASH ---
if "pagina_attiva" not in st.session_state: st.session_state["pagina_attiva"] = "🔥 Offerte del Mese"

if "lista_preventivi" not in st.session_state: st.session_state["lista_preventivi"] = []
if "lista_fascicolo" not in st.session_state: st.session_state["lista_fascicolo"] = [] 

st.session_state["lista_preventivi"] = [p for p in st.session_state.get("lista_preventivi", []) if isinstance(p, dict)]
st.session_state["lista_fascicolo"] = [p for p in st.session_state.get("lista_fascicolo", []) if isinstance(p, dict)]

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

# --- CLASSE PDF PREVENTIVATORE (VERTICALE) ---
class MaldarizziPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4') 
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(False)
        if os.path.exists("Rubik-Light.ttf"): self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
        if os.path.exists("Rubik-Bold.ttf"): self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
        self.f_f = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

    def header(self):
        if os.path.exists("sfondo_nero.jpeg"):
            try: self.image("sfondo_nero.jpg", 0, 0, 210, 297)
            except Exception: self.set_fill_color(20, 20, 20); self.rect(0, 0, 210, 297, 'F')
        else: self.set_fill_color(20, 20, 20); self.rect(0, 0, 210, 297, 'F')

        if os.path.exists("logo.png"):
            try: self.image("logo.png", 5, 5, 45) 
            except Exception: pass
            try: self.image("logo.png", 145, 275, 55)
            except Exception: pass

# --- CLASSE PDF FASCICOLO (ORIZZONTALE) ---
class FascicoloPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(True, margin=15)
        if os.path.exists("Rubik-Light.ttf"): self.add_font("Rubik", "", "Rubik-Light.ttf", uni=True)
        if os.path.exists("Rubik-Bold.ttf"): self.add_font("Rubik", "B", "Rubik-Bold.ttf", uni=True)
        self.f_f = "Rubik" if os.path.exists("Rubik-Light.ttf") else "Arial"

    def header(self):
        if os.path.exists("sfondo nero orizz.jpg"):
            try: self.image("sfondo nero orizz.jpg", 0, 0, 297, 210)
            except Exception: self.set_fill_color(20, 20, 20); self.rect(0, 0, 297, 210, 'F')
        elif os.path.exists("sfondo_nero.jpg"):
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
    
    if os.path.exists("logo.png"): st.sidebar.image("logo.png", width=180)
    st.sidebar.markdown(f"👤 Benvenuto, **{utente_loggato['nome']}**")
    st.sidebar.markdown(f"🏷️ Ruolo: *{utente_loggato['ruolo'].upper()}*")
    st.sidebar.markdown("---")
    
    if utente_loggato["ruolo"] == "admin":
        st.sidebar.markdown("### 📊 Pannello Direzione")
        if os.path.exists("statistiche_preventivi.csv"):
            df_stats = pd.read_csv("statistiche_preventivi.csv")
            st.sidebar.success(f"Totale Preventivi Generati: **{len(df_stats)}**")
            with open("statistiche_preventivi.csv", "rb") as f:
                st.sidebar.download_button("📥 Scarica Excel Statistiche", data=f, file_name="Statistiche_Maldarizzi.csv", mime="text/csv")
        else: st.sidebar.warning("Nessun preventivo registrato finora.")
        st.sidebar.markdown("---")

    opzioni_menu = ["🔥 Offerte del Mese", "🎯 Preventivatore Strumentale"]
    try: idx_menu = opzioni_menu.index(st.session_state["pagina_attiva"])
    except: idx_menu = 0
    menu_scelta = st.sidebar.radio("📌 MENU PRINCIPALE", opzioni_menu, index=idx_menu)
    if menu_scelta != st.session_state["pagina_attiva"]:
        st.session_state["pagina_attiva"] = menu_scelta
        st.rerun()
        
    st.sidebar.markdown("---")
    g_validita = st.sidebar.slider("Validità Offerta PDF (gg)", 1, 30, 30)
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Esci"):
        st.session_state["authenticated"] = False
        st.rerun()

    # ==========================================
    # SEZIONE 1: VETRINA PROMO E FASCICOLO
    # ==========================================
    if st.session_state["pagina_attiva"] == "🔥 Offerte del Mese":
        
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

                    pdf_fascicolo.set_text_color(255, 255, 255)
                    for p in st.session_state["lista_fascicolo"]:
                        if not isinstance(p, dict): continue 
                        
                        registra_statistica(nome_cons.upper(), p.get('cliente', ''), p['marca'], p['modello'], p['canone'], p['anticipo'], p['durata'], p['km'], "Fascicolo Promo")
                        
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
                    pdf_fascicolo.cell(0, 4, f"*Canone non comprende tassa automobilistica. Validita' offerta: {g_validita}gg.", align="L", ln=True)
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
            
            if st.session_state.get("pdf_carrello_pronto"):
                show_bananas()
                with open("Fascicolo_Offerte.pdf", "rb") as f:
                    st.download_button("📩 IL PDF E' PRONTO: SCARICA ORA!", f, "Fascicolo_Offerte.pdf", "application/pdf")
                    
            st.markdown("---")

        st.title("🔥 Promozioni del Mese")
        st.markdown("Sfoglia le offerte e trasferiscile nel preventivatore.")
        
        with st.sidebar.expander("📥 CARICAMENTO DATABASE PROMO", expanded=False):
            file_promo = st.file_uploader("1. Database Generico (.xlsx)", type=["xlsx", "csv"], key="file1")
            if file_promo:
                with open("promo_mese.xlsx", "wb") as f: f.write(file_promo.getbuffer())
                st.success("✅ DB Generico Aggiornato!")

            file_4v = st.file_uploader("2. File 4Vantage (.xlsx)", type=["xlsx", "csv"], key="file2")
            if file_4v:
                with open("promo_4vantage.xlsx", "wb") as f: f.write(file_4v.getbuffer())
                st.success("✅ DB 4Vantage Aggiornato!")
                
            st.markdown("---")
            if st.button("🗑️ Elimina tutti i Database"):
                if os.path.exists("promo_mese.xlsx"): os.remove("promo_mese.xlsx")
                if os.path.exists("promo_4vantage.xlsx"): os.remove("promo_4vantage.xlsx")
                st.success("✅ Vetrina svuotata con successo!")
                st.rerun()

        df_list = []
        
        if os.path.exists("promo_mese.xlsx"):
            try:
                df_main = leggi_file_dati("promo_mese.xlsx")
                df_main.columns = df_main.columns.str.strip().str.upper()
                if not df_main.empty: df_list.append(df_main)
            except: pass

        if os.path.exists("promo_4vantage.xlsx"):
            try:
                df_4v = leggi_file_dati("promo_4vantage.xlsx")
                df_4v.columns = df_4v.columns.str.strip().str.upper()
                if not df_4v.empty: df_list.append(df_4v)
            except Exception as e:
                pass

        if df_list:
            try:
                df_promo = pd.concat(df_list, ignore_index=True)
                df_promo = df_promo.fillna("") 
                
                c_search, c_tipo, c_alimen, c_player = st.columns([2, 1, 1, 1])
                with c_search:
                    ricerca = st.text_input("🔍 Cerca per marca o modello...").upper()
                
                with c_tipo:
                    if 'TIPOLOGIA CLIENTE' in df_promo.columns:
                        tipi_validi = set()
                        for x in df_promo['TIPOLOGIA CLIENTE'].unique():
                            if str(x).strip() and str(x).upper().strip() != 'NAN':
                                tipi_validi.add(str(x).upper().strip())
                        lista_tipi = ["Tutti"] + sorted(list(tipi_validi))
                        filtro_tipo = st.selectbox("👤 Cliente", lista_tipi)
                    else:
                        filtro_tipo = "Tutti"
                
                with c_alimen:
                    if 'ALIMENTAZIONE' in df_promo.columns:
                        alim_valide = set()
                        for x in df_promo['ALIMENTAZIONE'].unique():
                            if str(x).strip() and str(x).upper().strip() != 'NAN':
                                alim_valide.add(str(x).upper().strip())
                        lista_alimen = ["Tutte"] + sorted(list(alim_valide))
                        filtro_alimen = st.selectbox("⚡ Alimentazione", lista_alimen)
                    else:
                        filtro_alimen = "Tutte"
                        
                with c_player:
                    if 'PLAYER' in df_promo.columns:
                        player_validi = set()
                        for x in df_promo['PLAYER'].unique():
                            if str(x).strip() and str(x).upper().strip() != 'NAN':
                                player_validi.add(str(x).upper().strip())
                        lista_player = ["Tutti"] + sorted(list(player_validi))
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
                    tipo_cliente_off = str(row.get('TIPOLOGIA CLIENTE', '')).strip().upper() if 'TIPOLOGIA CLIENTE' in df_promo.columns else ""
                    
                    link_raw = str(row.get('LINK OFFERTA', '')).strip() if 'LINK OFFERTA' in df_promo.columns else str(row.get('link offerta', '')).strip()
                    link_valido = link_raw if link_raw.startswith("http") else ("https://" + link_raw if link_raw.startswith("www") else "")
                    
                    try: canone = float(str(row.get('CANONE', 0)).replace(' ', '').replace('€', '').replace(',','.'))
                    except: canone = 0.0
                    try: anticipo = float(str(row.get('ANTICIPO', 0)).replace(' ', '').replace('€', '').replace(',','.'))
                    except: anticipo = 0.0
                    try: mesi = int(float(str(row.get('MESI', 0)).replace(' ', '').replace(',','.')))
                    except: mesi = 0
                    try: km = int(float(str(row.get('KM TOTALI', 0)).replace(' ', '').replace(',','.')))
                    except: km = 0

                    if ricerca and ricerca not in marca and ricerca not in modello.upper(): continue
                    if filtro_alimen != "Tutte" and alimen != filtro_alimen: continue
                    if filtro_player != "Tutti" and player != filtro_player: continue
                    
                    if filtro_tipo != "Tutti":
                        if filtro_tipo == "PRIVATO" and tipo_cliente_off == "ENTRAMBI":
                            pass
                        elif filtro_tipo == "PARTITA IVA" and tipo_cliente_off == "ENTRAMBI":
                            pass
                        elif tipo_cliente_off != filtro_tipo:
                            continue
                        
                    offerte_filtrate.append({
                        "marca": marca, "modello": modello, "canone": canone, 
                        "anticipo": anticipo, "durata": mesi, "km_totali": km,
                        "tipo": offerta_tipo, "player": player, "comm": commissioni, 
                        "link": link_valido, "tipologia_cliente": tipo_cliente_off
                    })
                
                offerte_filtrate = sorted(offerte_filtrate, key=lambda x: x['canone'])

                if not offerte_filtrate:
                    st.warning("Nessuna offerta trovata con questi parametri.")
                else:
                    colonne_griglia = st.columns(3)
                    for idx, auto in enumerate(offerte_filtrate):
                        with colonne_griglia[idx % 3]:
                            link_html = f'<a href="{auto["link"]}" target="_blank" style="color: #C9BC41; text-decoration: none; font-size: 13px;">🔗 Apri Offerta Web</a>' if auto["link"] else '<span style="color: #888; font-size: 12px;">Nessun link web</span>'
                            
                            st.markdown(f"""
                            <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px;">
                                <h3 style="margin-bottom: 0; color: #FFF;">{auto['marca']}</h3>
                                <h5 style="margin-top: 0; color: #AAA;">{auto['modello']}</h5>
                                <h1 style="color: #C9BC41; margin-bottom: 5px;">Euro {str(auto['canone']).replace('.0','')} <span style="font-size: 14px; color: #888;"> /mese</span></h1>
                                <p style="color: #DDD; font-size: 14px; margin-bottom: 10px;">
                                    ⏳ {auto['durata']} mesi | 🛣️ {auto['km_totali']} Km totali<br>
                                    💰 Anticipo: Euro {str(auto['anticipo']).replace('.0','')}
                                </p>
                                <hr style="border-top: 1px solid #444; margin: 10px 0;">
                                <p style="font-size: 13px; color: #BBB; line-height: 1.4; margin-bottom: 5px;">
                                    🏢 <b>Player:</b> {auto['player']}<br>
                                    🏷️ <b>Tipo:</b> {auto['tipo']}<br>
                                    👤 <b>Cliente:</b> {auto['tipologia_cliente']}<br>
                                    💶 <b>Commissioni:</b> {auto['comm']}
                                </p>
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
                                    
                                    dur = auto['durata']
                                    st.session_state["val_km"] = int((auto['km_totali'] / dur) * 12) if dur > 0 else auto['km_totali']
                                    
                                    st.session_state["val_input_mode"] = "Testo Libero"
                                    st.session_state["origine_preventivo"] = "Vetrina Promo" 
                                    
                                    p_upper = auto['player'].upper()
                                    t_upper = auto['tipo'].upper()
                                    st.session_state["val_p_rca"] = "250 Euro"
                                    st.session_state["val_p_kasko"] = "500 Euro"
                                    st.session_state["val_usa_gomme"] = False
                                    st.session_state["val_tipo_gomme"] = "ILLIMITATE"
                                    st.session_state["val_n_gomme"] = 4
                                    st.session_state["val_stagione_gomme"] = "Estive"

                                    if "AYVENS" in p_upper:
                                        if "4VANTAGE" in t_upper or "4 VANTAGE" in t_upper:
                                            st.session_state["val_p_if"] = "0%"
                                            st.session_state["val_usa_gomme"] = True
                                            st.session_state["val_tipo_gomme"] = "A NUMERO"
                                            st.session_state["val_n_gomme"] = 4
                                            st.session_state["val_stagione_gomme"] = "Invernali"
                                        else: 
                                            st.session_state["val_p_if"] = "500 Euro"
                                    elif "ARVAL" in p_upper: 
                                        st.session_state["val_p_if"] = "500 Euro"
                                    elif "LEASYS" in p_upper or "SANTANDER" in p_upper or "ALPHABET" in p_upper: 
                                        st.session_state["val_p_if"] = "10%"
                                    else: 
                                        st.session_state["val_p_if"] = "10%"

                                    st.session_state["pagina_attiva"] = "🎯 Preventivatore Strumentale"
                                    st.rerun()

                            with c_btn2:
                                if st.button("🛒 Aggiungi al Carrello", key=f"btn_cart_{idx}"):
                                    dur = auto['durata']
                                    km_anno = int((auto['km_totali'] / dur) * 12) if dur > 0 else auto['km_totali']
                                    
                                    auto_carrello = {
                                        "marca": auto['marca'],
                                        "modello": auto['modello'],
                                        "canone": auto['canone'],
                                        "anticipo": auto['anticipo'],
                                        "durata": auto['durata'],
                                        "km": km_anno,
                                        "player": auto['player'],
                                        "tipo": auto['tipo']
                                    }
                                    st.session_state["lista_fascicolo"].append(auto_carrello)
                                    st.session_state["pdf_carrello_pronto"] = False 
                                    st.rerun()

            except Exception as e:
                st.error(f"Errore caricamento database: {str(e)}")
        else:
            st.info("👈 Apri il menù 'CARICAMENTO DATABASE PROMO' nel menù laterale per inserire i file.")

    # ==========================================
    # SEZIONE 2: PREVENTIVATORE (VERTICALE)
    # ==========================================
    elif st.session_state["pagina_attiva"] == "🎯 Preventivatore Strumentale":
        st.title("🎯 Preventivatore Strumentale (Con Motore Google)")
        
        st.sidebar.header("📥 Importa PDF Portale")
        pdf_portale = st.sidebar.file_uploader("Carica PDF (Arval, Leasys, Ayvens)", type=["pdf"])
        if pdf_portale and st.sidebar.button("🧠 Analizza e Compila Dati dal PDF"):
            try:
                pdf_bytes = io.BytesIO(pdf_portale.getvalue())
                reader = pypdf.PdfReader(pdf_bytes)
                testo_flat = re.sub(r'\s+', ' ', "".join([p.extract_text() for p in reader.pages])).strip()
                testo_upper = testo_flat.upper()
                st.session_state["debug_text"] = testo_flat
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
            st.sidebar.success("Database aggiornato!")

        if os.path.exists("dati.xlsx"):
            excel = pd.ExcelFile("dati.xlsx")
            foglio = st.sidebar.selectbox("Seleziona Categoria", excel.sheet_names)
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
            foto_m = st.file_uploader("Foto Auto (Se vuoto usa CarsXE)", type=["jpg", "png", "jpeg"])

        st.markdown("---")
        st.subheader("🛡️ Servizi e Penali")
        s1, s2, s3 = st.columns(3)
        
        with s1:
            rca_options = ["0 Euro", "250 Euro", "500 Euro"]
            rca_idx = rca_options.index(st.session_state.get("val_p_rca", "250 Euro")) if st.session_state.get("val_p_rca", "250 Euro") in rca_options else 1
            p_rca = st.selectbox("Penale RCA", rca_options, index=rca_idx)
            if_options = ["0%", "5%", "10%", "20%", "250 Euro", "500 Euro", "1000 Euro", "a carico cliente"]
            if_idx = if_options.index(st.session_state.get("val_p_if", "10%")) if st.session_state.get("val_p_if", "10%") in if_options else 2
            p_if = st.selectbox("Penale Incendio/Furto", if_options, index=if_idx)
        
        with s2:
            kasko_options = ["0 Euro", "250 Euro", "500 Euro", "1000 Euro", "a carico cliente"]
            kasko_idx = kasko_options.index(st.session_state.get("val_p_kasko", "500 Euro")) if st.session_state.get("val_p_kasko", "500 Euro") in kasko_options else 2
            p_kasko = st.selectbox("Penale Danni/Kasko", kasko_options, index=kasko_idx)
            infort = st.checkbox("Infortunio Conducente (PAI)", value=True)
            usa_vett_sost = st.checkbox("Vettura Sostitutiva?", value=False)
            vett_sost_cat = st.selectbox("Categoria Sostitutiva", ["ECONOMY", "FAMILY SMALL", "FAMILY LARGE", "EXECUTIVE", "LUXURY"]) if usa_vett_sost else None
        
        with s3:
            usa_gomme = st.checkbox("Includere Pneumatici?", value=st.session_state.get("val_usa_gomme", False))
            g_num = "ILLIMITATE"
            
            if usa_gomme:
                valore_memoria = str(st.session_state.get("val_tipo_gomme", "ILLIMITATE"))
                idx_g = 1 if valore_memoria == "A NUMERO" else 0
                
                g_tipo = st.radio("Tipo Gomme", ["ILLIMITATE", "A NUMERO"], horizontal=True, index=idx_g)
                
                if g_tipo == "A NUMERO":
                    c_g1, c_g2 = st.columns([1, 2])
                    with c_g1:
                        n_gomme = st.number_input("Numero", value=int(st.session_state.get("val_n_gomme", 4)), min_value=1)
                    with c_g2:
                        stag_opts = ["Estive", "Invernali", "All Season"]
                        val_stag = str(st.session_state.get("val_stagione_gomme", "Estive"))
                        stag_idx = stag_opts.index(val_stag) if val_stag in stag_opts else 0
                        stagione_gomme = st.selectbox("Stagione", stag_opts, index=stag_idx)
                        
                    g_num = f"{n_gomme} {stagione_gomme}"
                    st.session_state["val_tipo_gomme"] = "A NUMERO"
                    st.session_state["val_n_gomme"] = n_gomme
                    st.session_state["val_stagione_gomme"] = stagione_gomme
                else:
                    g_num = "ILLIMITATE"
                    st.session_state["val_tipo_gomme"] = "ILLIMITATE"
            else: 
                g_num = None
                st.session_state["val_usa_gomme"] = False

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
        if st.button("➕ AGGIUNGI AL DOCUMENTO"):
            foto_bytes = foto_m.getvalue() if foto_m else None
            if not foto_bytes:
                with st.spinner('Ricerca immagine su Google in corso...'):
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
            st.rerun()

        if len(st.session_state["lista_preventivi"]) > 0:
            st.info(f"🛒 **{len(st.session_state['lista_preventivi'])}** veicoli nel preventivo.")
            col_stampa, col_svuota = st.columns([2, 1])
            with col_svuota:
                if st.button("🗑️ Svuota Lista"):
                    st.session_state["lista_preventivi"] = []
                    st.rerun()
            with col_stampa:
                if st.button("🚀 STAMPA PREVENTIVO UNICO"):
                    pdf = MaldarizziPDF()
                    for i, p in enumerate(st.session_state["lista_preventivi"]):
                        if not isinstance(p, dict): continue 
                        
                        registra_statistica(nome_cons.upper(), p['cliente'], p['marca'], p['versione'], p['canone'], p['anticipo'], p['durata'], p['km'], p['origine_dati'])
                        pdf.add_page()
                        pdf.set_y(20); pdf.set_font(pdf.f_f, "", 12); pdf.set_text_color(200, 200, 200); pdf.cell(0, 5, "Spettabile cliente:", align="C", ln=True)
                        pdf.set_font(pdf.f_f, "B", 16); pdf.set_text_color(255, 255, 255); pdf.cell(0, 7, pulisci_testo(p['cliente'].upper()), align="C", ln=True)
                        
                        # --- STAMPA MARCA E VERSIONE (Alzato e rimpicciolito per evitare sovrapposizioni) ---
                        pdf.set_y(36); pdf.set_font(pdf.f_f, "B", 22); pdf.multi_cell(0, 9, pulisci_testo(f"{p['marca']} {p['versione']}"), align="C")
                        
                        # --- NUOVA RIGA: VEICOLO NUOVO/USATO (Centrato perfettamente) ---
                        pdf.set_x(10) 
                        pdf.set_font(pdf.f_f, "B", 12)
                        pdf.set_text_color(201, 188, 65)
                        stato_veicolo = str(p.get('t_veicolo', 'Nuovo')).upper()
                        pdf.cell(0, 6, f"VEICOLO {stato_veicolo}", align="C", ln=True)
                        
                        if p.get("foto_bytes"):
                            f_path = f"tmp_multi_{i}.jpg" 
                            with open(f_path, "wb") as f: f.write(p["foto_bytes"])
                            try: pdf.image(f_path, 25, pdf.get_y() + 2, 160)
                            except Exception as e: st.error("L'immagine di Google ha un formato incompatibile col PDF.")
                        
                        pdf.set_y(155); pdf.set_font(pdf.f_f, "B", 50); pdf.set_text_color(201, 188, 65)
                        pdf.cell(0, 15, pulisci_testo(f"Euro {str(p['canone']).replace('.0','')} / mese"), align="C", ln=True)
                        pdf.set_y(180); pdf.set_font(pdf.f_f, "B", 11); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(40, 40, 40)
                        
                        voci = [f"{p['durata']} mesi", f"Km {int(p['km']) * int(p['durata']) // 12}", f"Anticipo {str(p['anticipo']).replace('.0','')}", p['iva_text']]
                        start_x = (210 - (42 * 4 + 4 * 3)) / 2
                        for idx, voce in enumerate(voci):
                            pdf.set_xy(start_x + (42 + 4) * idx, 180); pdf.cell(42, 10, pulisci_testo(voce), align="C", fill=True)
                        
                        pdf.set_y(202); pdf.set_font(pdf.f_f, "B", 11); pdf.set_x(10); pdf.cell(0, 6, "SERVIZI INCLUSI NEL CANONE", ln=True, align="C")
                        pdf.set_font(pdf.f_f, "", 9)
                        
                        serv_list = [
                            f"RCA (Franchigia {p['p_rca']})", 
                            f"Incendio/Furto (Franchigia {p['p_if']})", 
                            f"Danni/Kasko (Franchigia {p['p_kasko']})", 
                            "Manutenzione Ordinaria/Straordinaria", 
                            "Assistenza Stradale H24"
                        ]
                        if p.get('g_num'): serv_list.append(f"Gomme: {p['g_num']}")
                        if p.get('infort'): serv_list.append("Infortunio Conducente (PAI)")
                        if p.get('vett_sost'): serv_list.append(f"Vettura Sostitutiva ({p['vett_sost']})")
                        
                        pdf.set_x(10); pdf.multi_cell(0, 5, pulisci_testo(" | ".join(serv_list)), align="C")

                        # STAMPA DEGLI OPTIONAL
                        testo_opt = str(p.get('opt', '')).strip()
                        if testo_opt:
                            pdf.ln(2)
                            pdf.set_font(pdf.f_f, "B", 10)
                            pdf.set_text_color(201, 188, 65)
                            pdf.cell(0, 5, "OPTIONAL INCLUSI", ln=True, align="C")
                            pdf.set_font(pdf.f_f, "", 8)
                            pdf.set_text_color(255, 255, 255)
                            pdf.multi_cell(0, 4, pulisci_testo(testo_opt), align="C")

                        # STAMPA DELLE NOTE AGGIUNTIVE
                        testo_note = str(p.get('note', '')).strip()
                        if testo_note:
                            pdf.ln(2)
                            pdf.set_font(pdf.f_f, "B", 10)
                            pdf.set_text_color(201, 188, 65)
                            pdf.cell(0, 5, "NOTE AGGIUNTIVE", ln=True, align="C")
                            pdf.set_font(pdf.f_f, "", 8)
                            pdf.set_text_color(255, 255, 255)
                            pdf.multi_cell(0, 4, pulisci_testo(testo_note), align="C")

                        # DISCLAIMER E FOOTER
                        pdf.ln(4)
                        pdf.set_font(pdf.f_f, "I", 7)
                        pdf.set_text_color(180, 180, 180)
                        pdf.multi_cell(0, 3, f"*Le immagini sono puramente indicative e non costituiscono vincolo contrattuale.\n*ATTENZIONE: il canone indicato non comprende la tassa automobilistica, da gennaio 2020 a carico del cliente per modifica di legge (D.L. 124/2019).\n*Validità offerta: {g_validita} giorni.", align="C")
                        
                        pdf.set_y(255); pdf.set_font(pdf.f_f, "B", 10); pdf.set_text_color(255, 255, 255)
                        pdf.cell(0, 5, f"CONSULENTE: {nome_cons.upper()}", align="C", ln=True)
                        pdf.set_font(pdf.f_f, "", 9); pdf.set_text_color(200, 200, 200)
                        pdf.cell(0, 5, f"E-mail: {email_cons}  |  Tel: {tel_cons}", align="C", ln=True)

                    pdf.output("preventivo_multiplo.pdf")
                    with open("preventivo_multiplo.pdf", "rb") as f:
                        st.download_button("📩 SCARICA PREVENTIVO", f, "Offerta.pdf", key="dl_multi")
