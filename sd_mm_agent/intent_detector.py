"""
SD/MM Agent - Intent Detection (Niyet Tespiti) Modulu.

Kullanicinin sorusunu analiz ederek SQL mi yoksa BAPI islemi mi
istedigini belirler. LLM tabanli siniflandirma yapar.

Akis:
  Kullanici sorusu → LLM (gpt-4o-mini, deterministik) → "SQL" veya "BAPI"

Ornekler:
  "Tum malzemeleri listele"          → SQL
  "Stoku 100'den fazla olanlar"      → SQL
  "Malzeme olusturmak istiyorum"     → BAPI
  "Satin alma siparisi acmak lazim"  → BAPI
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import OPENAI_MODEL
from sd_mm_agent.prompts import INTENT_DETECTION_PROMPT
from token_tracker import log_token_usage


def _get_api_key() -> str:
    """API anahtarini taze okur (st.secrets veya .env)."""
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    try:
        _env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(_env_path, override=True)
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


# ══════════════════════════════════════════════════════════════════════
# INTENT DETECTION - Kullanici Niyetini Tespit Et
# ══════════════════════════════════════════════════════════════════════
# LLM'e kisa bir prompt gonderilir ve sadece "SQL" veya "BAPI" yaniti
# beklenir. Deterministik sonuc icin temperature=0.0 kullanilir.
#
# Bu adim SD/MM Agent'in orkestrasyon mantigi icin kritiktir:
# - SQL → sql_agent.generator.generate_sql() cagirilir
# - BAPI → bapi_agent.generator.generate_bapi_response() cagirilir
# ══════════════════════════════════════════════════════════════════════


def detect_intent(question: str) -> str:
    """
    Kullanicinin sorusunun SQL mi yoksa BAPI islemi mi oldugunu belirler.

    ── INTENT DETECTION: LLM ile niyet siniflandirma ──
    gpt-4o-mini modeli kullanilarak deterministik siniflandirma yapilir.
    max_tokens=10 ile sadece kisa bir yanit beklenir.

    Args:
        question: Kullanicinin Turkce sorusu
            Ornek: "Stoku 100'den fazla olan malzemeleri goster"

    Returns:
        "SQL" veya "BAPI" string'i
    """
    api_key = _get_api_key()
    if not api_key:
        # API key yoksa varsayilan olarak SQL dondur
        return "SQL"

    try:
        client = OpenAI(api_key=api_key)

        # ── LLM'e intent sorusunu gonder ──
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": INTENT_DETECTION_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.0,     # Deterministik yanit (her seferinde ayni sonuc)
            max_tokens=10,       # Sadece "SQL" veya "BAPI" bekliyoruz
        )

        # Token kullanimi kaydet
        try:
            usage = response.usage
            if usage:
                log_token_usage(
                    agent_adi="SD/MM Agent",
                    model=OPENAI_MODEL,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="Intent Tespiti",
                )
        except Exception:
            pass

        # ── Yaniti parse et ──
        result = response.choices[0].message.content.strip().upper()

        # Guvenlik: Sadece "SQL" veya "BAPI" kabul et
        if "BAPI" in result:
            return "BAPI"
        else:
            return "SQL"  # Varsayilan: SQL

    except Exception:
        # Hata durumunda varsayilan olarak SQL dondur
        return "SQL"
