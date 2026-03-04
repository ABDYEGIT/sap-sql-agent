"""
Yorglass SAP AI Platform - Ana Uygulama.

Sidebar'da agent secimi ile farkli SAP AI agent'larini calistirir.
Mevcut Agent'lar:
  1. SQL Generator Agent - Dogal dilden SAP Open SQL sorgusu uretimi
  2. BAPI Asistani Agent - BAPI parametre doldurma rehberi
  3. SD/MM Agent - SQL ve BAPI agent'larini orkestre eden birlesik agent
  4. Fis Okuyucu Agent - GPT-4o Vision ile fis gorseli okuma ve masraf kaydi
  5. IK Asistani Agent - IK dokumanlari uzerinde RAG tabanli soru-cevap
"""
import sys
from pathlib import Path

# Modul import'lari icin path ayarla
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from config import APP_TITLE, APP_ICON
from styles import inject_platform_css

# ============================
# SAYFA AYARLARI
# ============================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
)
inject_platform_css()

# ============================
# SIDEBAR - Agent Secimi
# ============================
with st.sidebar:
    # Agent secim listesi
    st.subheader("Agent Secimi")
    agent_options = {
        "SQL Generator": "sql",
        "BAPI Asistani": "bapi",
        "SD/MM Agent": "sdmm",
        "Fis Okuyucu": "receipt",
        "IK Asistani": "ik",
    }
    selected_agent_label = st.selectbox(
        "Calismak istediginiz agent'i secin:",
        options=list(agent_options.keys()),
        key="selected_agent",
        label_visibility="collapsed",
    )
    selected_agent = agent_options[selected_agent_label]

    st.divider()

    # Mimari butonu
    if st.button("Proje Mimarisi", use_container_width=True, key="btn_arch"):
        st.session_state["show_architecture"] = True
        st.rerun()
    if st.session_state.get("show_architecture"):
        if st.button("Agentlara Don", use_container_width=True, key="btn_back"):
            st.session_state["show_architecture"] = False
            st.rerun()

    st.divider()

# ============================
# SECILEN AGENT'I CALISTIR
# ============================
if st.session_state.get("show_architecture"):
    from architecture_page import render_architecture_page
    render_architecture_page()

elif selected_agent == "sql":
    from sql_agent.page import render_sql_agent
    render_sql_agent()

elif selected_agent == "bapi":
    from bapi_agent.page import render_bapi_agent
    render_bapi_agent()

elif selected_agent == "sdmm":
    from sd_mm_agent.page import render_sdmm_agent
    render_sdmm_agent()

elif selected_agent == "receipt":
    from receipt_agent.page import render_receipt_agent
    render_receipt_agent()

elif selected_agent == "ik":
    from ik_agent.page import render_ik_agent
    render_ik_agent()
