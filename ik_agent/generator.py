"""
IK Agent - Cevap Uretici Modulu.

RAG pipeline'inin son asamasi: Retrieval sonuclarini context olarak
LLM'e gonderir ve kaynak bilgileriyle birlikte cevap uretir.

RAG Pipeline:
1. RETRIEVAL  : rag_engine.search() → en yakin dokuman chunk'lari
2. AUGMENTATION: Chunk'lari system prompt'a context olarak ekle
3. GENERATION : LLM cevap uretir + kaynak listesi dondurur
"""
import os

from openai import OpenAI

from ik_agent.prompts import IK_SYSTEM_PROMPT
from config import OPENAI_MODEL, TEMPERATURE, MAX_TOKENS_RESPONSE


def _get_api_key() -> str:
    """API key cozumle."""
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        _env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(_env_path, override=True)
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


def generate_ik_response(
    question: str,
    rag_engine,
    chat_history: list = None,
) -> tuple:
    """
    IK sorusuna RAG tabanli cevap uretir.

    Args:
        question: Kullanicinin sorusu
        rag_engine: RAGEngine instance (arama icin)
        chat_history: Onceki sohbet mesajlari

    Returns:
        (response_text, sources) tuple'i
        - response_text: LLM'in urettigi cevap metni
        - sources: Kullanilan kaynaklarin listesi
          [{"section_title": "...", "source_file": "...", "text_preview": "...", "score": 0.89}]
    """
    api_key = _get_api_key()
    if not api_key:
        return "API anahtari bulunamadi.", []

    # ══════════════════════════════════════════
    # RAG ADIM 1: RETRIEVAL - Vector Search
    # ══════════════════════════════════════════
    sources = []
    context_text = ""

    if rag_engine:
        search_results = rag_engine.search(question, top_k=5)

        for result in search_results:
            source_info = {
                "section_title": result.get("metadata", {}).get("section_title", "Bilinmiyor"),
                "source_file": result.get("metadata", {}).get("source_file", "Bilinmiyor"),
                "text_preview": result.get("text", "")[:200],
                "score": result.get("score", 0),
            }
            sources.append(source_info)

        # Context olustur
        context_parts = []
        for i, result in enumerate(search_results):
            section = result.get("metadata", {}).get("section_title", "")
            text = result.get("text", "")
            context_parts.append(f"--- Kaynak {i+1} [{section}] ---\n{text}")

        context_text = "\n\n".join(context_parts)

    if not context_text:
        context_text = "(Dokumanda ilgili bilgi bulunamadi)"

    # ══════════════════════════════════════════
    # RAG ADIM 2: AUGMENTATION - Context Injection
    # ══════════════════════════════════════════
    system_prompt = IK_SYSTEM_PROMPT.format(context=context_text)

    # ══════════════════════════════════════════
    # RAG ADIM 3: GENERATION - LLM Cevap Uretimi
    # ══════════════════════════════════════════
    messages = [{"role": "system", "content": system_prompt}]

    # Chat gecmisini ekle
    if chat_history:
        for msg in chat_history[-6:]:  # Son 6 mesaj
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

    messages.append({"role": "user", "content": question})

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS_RESPONSE,
    )

    response_text = response.choices[0].message.content.strip()

    return response_text, sources
