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
if "val_input_mode" not in st.session_state: st.session_state["val_input_mode"] = "Da Listino"
if "val_marca_stampa" not in st.session_state: st.session_state["val_marca_stampa"] = ""
if "val_versione_stampa" not in st.session_state: st.session_state["val_versione_stampa"] = ""
if "val_p_rca" not in st.session_state: st.session_state["val_p_rca"] = "250 Euro"
if "val_p_if" not in st.session_state: st.session_state["val_p_if"] = "10%"
if "val_p_kasko" not in st.session_state: st.session_state["val_p_kasko"] = "500 Euro"
if "debug_text" not in st.session_state: st.session_state["debug_text"] = ""
if "val_note" not in st.session_state: st.session_state["val_note"] = ""

if check_password():
    # --- 2. CLASSE PDF (LAYOUT CON SFONDO SCURO) ---
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
                except Exception:
                    pass

            if os.path.exists("logo.png"):
                try:
                    self.image("logo.png", 145, 275, 55)
                except Exception:
                    pass

    # --- 3. INTERFACCIA STREAMLIT ---
    st.set_page_config(page_title="Maldarizzi Copilota", layout="wide")
    try: locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")
    except: pass

    st.sidebar.header("📥 Importa PDF Portale")
    pdf_portale = st.sidebar.file_uploader("Carica PDF (Arval, Leasys, Ayvens)", type=["pdf"])
    
    if pdf_portale and st.sidebar.button("🧠 Analizza e Compila Dati"):
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

            # --- ESTRATTORE CHIRURGICO ---
            if "AYVENS" in testo_upper or "SOCIETE GENERALE" in testo_upper or "ALD AUTOMOTIVE" in testo_upper:
                
                # 1. NUOVA ESTRAZIONE CLIENTE AYVENS (Più flessibile, gestisce con e senza virgola)
                m_cli = re.search(r':\s*([A-Za-z\s\,\'\.\-]+?)\s*\d{6,9}/\d{2,3}', testo_flat)
                if m_cli: 
                    nome_raw = m_cli.group(1).strip()
                    # Se c'è la virgola, pulisce l'eventuale doppio cognome
                    if "," in nome_raw:
                        nome_raw = nome_raw.split(",")[0].strip()
                        parti = nome_raw.split()
                        if len(parti) > 2 and parti[-1] == parti[-2]:
                            nome_raw = " ".join(parti[:-1])
                    st.session_state["val_cliente"] = nome_raw.upper()

                # 2. VEICOLO
                m_vei = re.search(r'Venduto\s+(?:[A-Z0-9]+\s+)?(.*?)\s+\d{2}/\d{2}/\d{4}', testo_flat, re.IGNORECASE)
                if m_vei:
                    vei = m_vei.group(1).strip()
                    if vei.endswith('.'): vei = vei[:-1].strip()
                    st.session_state["val_versione_stampa"] = vei
                    parti = vei.split()
                    if len(parti) > 0:
                        st.session_state["val_marca_stampa"] = parti[0].upper()

                # 3. DURATA E KM
                m_dur_km = re.search(r'\b(24|36|48|60)\s+(\d{4,7})\s+€', testo_flat)
                if m_dur_km:
                    st.session_state["val_durata"] = int(m_dur_km.group(1))
                    km_tot = int(m_dur_km.group(2))
                    if st.session_state["val_durata"] > 0:
                        st.session_state["val_km"] = int((km_tot / st.session_state["val_durata"]) * 12)

                # 4. CANONE E ANTICIPO
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
                if m_ant:
                    st.session_state["val_anticipo"] = float(m_ant.group(1).replace(',', '.'))

            elif "LEASYS" in testo_upper:
                m_cli = re.search(r'VENDITA\s+(.*?)\s+MALDARIZZI', testo_flat, re.IGNORECASE)
                if m_cli: 
                    st.session_state["val_cliente"] = m_cli.group(1).replace("SRL", "").replace("SPA", "").strip()

                m_marca = re.search(r'Marca\s+([A-Za-z0-9\-]+)', testo_flat, re.IGNORECASE)
                if m_marca:
                    st.session_state["val_marca_stampa"] = m_marca.group(1).upper().strip()
                
                m_ver = re.search(r'Versione\s+(.*?)\s+Canone Totale', testo_flat, re.IGNORECASE)
                if m_ver:
                    st.session_state["val_versione_stampa"] = m_ver.group(1).strip()

                m_dur = re.search(r'Durata\s+(\d{2,3})', testo_flat, re.IGNORECASE)
                if m_dur: st.session_state["val_durata"] = int(m_dur.group(1))

                m_km = re.search(r'km totali\s+([\d\s]+)\b', testo_flat, re.IGNORECASE)
                if m_km:
                    km_tot = int(m_km.group(1).replace(' ', ''))
                    if st.session_state["val_durata"] > 0:
                        st.session_state["val_km"] = int((km_tot / st.session_state["val_durata"]) * 12)

                m_can = re.search(r'Canone Totale\s+€\s*(\d{1,4}[,.]\d{2})', testo_flat, re.IGNORECASE)
                if m_can: st.session_state["val_canone"] = float(m_can.group(1).replace(',', '.'))
                    
                m_ant = re.search(r'Anticipo\s*€\s*([\d\s]+[,.]\
