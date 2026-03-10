"""
SQL Agent - LLM ile SAP Open SQL Sorgusu Uretimi.

OpenAI API kullanarak dogal dil sorusundan SAP Open SQL sorgusu uretir.
Multi-DB destegi: SAP (transactional) ve BW (Business Warehouse).

RAG ENTEGRASYONU:
- find_relevant_tables_with_rag() ile vector search yapilir
- Bulunan tablolar format_metadata_for_prompt() ile prompt'a eklenir
- LLM bu zenginlestirilmis prompt ile SQL uretir
  (RAG ADIM 4: GENERATION)
"""
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import OPENAI_MODEL, MAX_CHAT_HISTORY, MAX_TOKENS_RESPONSE, TEMPERATURE
from sql_agent.prompts import get_system_prompt
from sql_agent.bw_prompts import get_bw_system_prompt
from sql_agent.metadata_loader import (
    find_relevant_tables_with_rag,
    format_metadata_for_prompt,
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
# RAG ADIM 4: GENERATION - Zenginlestirilmis Prompt ile SQL Uretimi
# ══════════════════════════════════════════════════════════════════════
# Bu fonksiyon RAG pipeline'inin son adimini gerceklestirir:
# 1. Vector search ile bulunan tablolar (RETRIEVAL sonucu)
# 2. Bu tablolarin metadata'si prompt'a eklenir (AUGMENTATION)
# 3. LLM bu zenginlestirilmis prompt ile SQL sorgusu uretir (GENERATION)
# ══════════════════════════════════════════════════════════════════════

def generate_sql(
    question: str,
    tables: dict,
    relationships: list,
    chat_history: list,
    rag_engine=None,
    db_type: str = "SAP",
) -> tuple:
    """
    Dogal dil sorusundan SAP Open SQL sorgusu uretir.

    ── RAG GENERATION: Vector search sonuclari + LLM = SQL sorgusu ──

    Args:
        question: Kullanicinin Turkce sorusu
        tables: Metadata dict (tablo -> alanlar)
        relationships: Iliski listesi
        chat_history: Onceki mesajlar
        rag_engine: RAGEngine instance (None ise tum tablolar kullanilir)
        db_type: Hedef veritabani ("SAP" veya "BW")

    Returns:
        (full_response_text, list_of_used_table_names)
    """
    api_key = _get_api_key()
    if not api_key:
        return "API anahtari bulunamadi. .env dosyanizi kontrol edin.", []

    # ── RAG ADIM 2+3: RETRIEVAL + AUGMENTATION ──
    # Vector search ile ilgili tablolari bul ve prompt'a ekle
    if rag_engine is not None:
        # VECTOR SEARCH ile en yakin tablolari bul
        relevant_tables, relevant_rels = find_relevant_tables_with_rag(
            tables, relationships, question, rag_engine
        )
    else:
        # RAG yoksa tum tablolari kullan (fallback)
        relevant_tables = tables
        relevant_rels = relationships

    if not relevant_tables:
        relevant_tables = tables
        relevant_rels = relationships

    # ── AUGMENTATION: Bulunan tablolari LLM prompt'una ekle ──
    metadata_text = format_metadata_for_prompt(relevant_tables, relevant_rels)

    # DB tipine gore uygun prompt sec
    if db_type.upper() == "BW":
        system_prompt = get_bw_system_prompt(metadata_text)
    else:
        system_prompt = get_system_prompt(metadata_text)

    messages = [{"role": "system", "content": system_prompt}]

    # Chat gecmisini ekle (son N mesaj)
    recent = chat_history[-MAX_CHAT_HISTORY:]
    for msg in recent:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    try:
        # ── GENERATION: LLM ile SQL uret ──
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
                    agent_adi="SQL Generator",
                    model=OPENAI_MODEL,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="SQL Uretimi",
                )
        except Exception:
            pass

        content = response.choices[0].message.content

        # Yanittan kullanilan tablolari cikart
        used_tables = extract_used_tables(content, tables)

        return content, used_tables

    except Exception as e:
        return f"Hata olustu: {e}", []


def extract_used_tables(response: str, all_tables: dict) -> list:
    """
    LLM yanitindan kullanilan tablo adlarini cikarir.

    Strateji:
    1. ```abap ... ``` blogundan SQL'i parse et
    2. FROM ve JOIN sonrasi tablo adlarini bul
    3. Bilinen tablo adlariyla karsilastir
    """
    used = set()

    # abap code blogundan SQL'i cikart
    code_match = re.search(r"```abap\s*(.*?)\s*```", response, re.DOTALL)
    if code_match:
        sql_text = code_match.group(1).upper()
        for table_name in all_tables:
            if re.search(rf"\b{re.escape(table_name.upper())}\b", sql_text):
                used.add(table_name)

    # Fallback: tum yanit icerisinde tablo adlarini ara
    if not used:
        upper_response = response.upper()
        for table_name in all_tables:
            if table_name.upper() in upper_response:
                used.add(table_name)

    return list(used)


def extract_sql_block(response: str):
    """Yanittan ```abap ... ``` code blogunu cikarir."""
    match = re.search(r"```abap\s*(.*?)\s*```", response, re.DOTALL)
    return match.group(1).strip() if match else None
