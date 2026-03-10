"""
Yorglass SAP AI Platform - Konfigurasyon.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(_env_path, override=True)
except ImportError:
    pass

# API key: once st.secrets, sonra env var
def _resolve_api_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")

OPENAI_API_KEY = _resolve_api_key()
OPENAI_MODEL = "gpt-4o-mini"

# ── Embedding modeli (RAG / Vector Search icin) ──
# text-embedding-3-small: 1536 boyutlu vektor, ucuz ve hizli
EMBEDDING_MODEL = "text-embedding-3-small"

# ── Vision modeli (Fis Okuyucu Agent - gorsel analiz icin) ──
# gpt-4o-mini: gorsel destekli, hizli ve ucuz (Temmuz 2024+)
VISION_MODEL = "gpt-4o-mini"

# Platform ayarlari
APP_TITLE = "Yorglass SAP AI Platform"
APP_ICON = "\U0001f3ed"  # Fabrika emoji
MAX_CHAT_HISTORY = 10
MAX_TOKENS_RESPONSE = 2000
TEMPERATURE = 0.2

# ── Multi-DB Metadata Dosya Yollari ──
SAP_METADATA_EXCEL = "sql_agent/data/sap_metadata.xlsx"
BW_METADATA_EXCEL = "sql_agent/data/bw_metadata.xlsx"
