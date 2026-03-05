"""
BAPI Agent - LLM ile BAPI Oneri ve Parametre Doldurma Ornegi Uretimi.

OpenAI API kullanarak kullanicinin istedigi isleme uygun BAPI'yi bulur
ve parametrelerin nasil doldurulacagini orneklerle gosterir.

RAG ENTEGRASYONU:
- find_relevant_bapis_with_rag() ile vector search yapilir
- Bulunan BAPI'ler format_bapi_metadata_for_prompt() ile prompt'a eklenir
- LLM bu zenginlestirilmis prompt ile BAPI onerisi uretir
  (RAG ADIM 4: GENERATION)
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import OPENAI_MODEL, MAX_CHAT_HISTORY, MAX_TOKENS_RESPONSE, TEMPERATURE
from bapi_agent.prompts import get_bapi_system_prompt
from bapi_agent.metadata_loader import (
    find_relevant_bapis_with_rag,
    format_bapi_metadata_for_prompt,
)
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
# RAG ADIM 4: GENERATION - Zenginlestirilmis Prompt ile BAPI Onerisi
# ══════════════════════════════════════════════════════════════════════

def generate_bapi_response(
    question: str,
    bapis: dict,
    chat_history: list,
    rag_engine=None,
) -> tuple:
    """
    Kullanicinin sorusuna gore uygun BAPI'yi bulur ve nasil kullanilacagini gosterir.

    ── RAG GENERATION: Vector search sonuclari + LLM = BAPI onerisi ──

    Args:
        question: Kullanicinin Turkce sorusu (ornek: "malzeme genisletmek istiyorum")
        bapis: BAPI metadata dict'i
        chat_history: Onceki mesajlar
        rag_engine: RAGEngine instance (None ise tum BAPI'ler kullanilir)

    Returns:
        (full_response_text, list_of_used_bapi_names)
    """
    api_key = _get_api_key()
    if not api_key:
        return "API anahtari bulunamadi. .env dosyanizi kontrol edin.", []

    # ── RAG ADIM 2+3: RETRIEVAL + AUGMENTATION ──
    if rag_engine is not None:
        # VECTOR SEARCH ile en yakin BAPI'leri bul
        relevant_bapis = find_relevant_bapis_with_rag(
            bapis, question, rag_engine
        )
    else:
        relevant_bapis = bapis

    if not relevant_bapis:
        relevant_bapis = bapis

    # ── AUGMENTATION: Bulunan BAPI'leri LLM prompt'una ekle ──
    metadata_text = format_bapi_metadata_for_prompt(relevant_bapis)
    system_prompt = get_bapi_system_prompt(metadata_text)

    messages = [{"role": "system", "content": system_prompt}]

    recent = chat_history[-MAX_CHAT_HISTORY:]
    for msg in recent:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    try:
        # ── GENERATION: LLM ile BAPI onerisi uret ──
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_RESPONSE,
        )

        # Token kullanimi kaydet
        try:
            usage = response.usage
            if usage:
                log_token_usage(
                    agent_adi="BAPI Asistani",
                    model=OPENAI_MODEL,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="BAPI Onerisi",
                )
        except Exception:
            pass

        content = response.choices[0].message.content

        used_bapis = extract_used_bapis(content, bapis)

        return content, used_bapis

    except Exception as e:
        return f"Hata olustu: {e}", []


def extract_used_bapis(response: str, all_bapis: dict) -> list:
    """LLM yanitindan kullanilan BAPI adlarini cikarir."""
    used = set()
    upper_response = response.upper()
    for bapi_name in all_bapis:
        if bapi_name.upper() in upper_response:
            used.add(bapi_name)
    return list(used)


def extract_abap_block(response: str):
    """Yanittan ```abap ... ``` code blogunu cikarir."""
    match = re.search(r"```abap\s*(.*?)\s*```", response, re.DOTALL)
    return match.group(1).strip() if match else None
