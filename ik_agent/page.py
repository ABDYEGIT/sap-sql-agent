"""
IK Agent - Streamlit Sayfa Modulu.

IK Asistani agent'inin chat arayuzunu render eder.
Sol tarafta sohbet, sag tarafta kaynak gosterim paneli.

Layout: st.columns([2, 1])
  Sol: Chat mesajlari + input
  Sag: Son yanittan gelen kaynak referanslari
"""
from pathlib import Path

import streamlit as st

from ik_agent.document_loader import load_and_chunk_docx, get_default_document_path
from ik_agent.generator import generate_ik_response, _get_api_key
from rag_engine import RAGEngine


# ══════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSIYONLAR
# ══════════════════════════════════════════════════════════════════════


def _get_rag_engine():
    """IK Agent icin RAG motorunu dondurur."""
    if "ik_rag_engine" not in st.session_state:
        api_key = _get_api_key()
        if api_key:
            st.session_state["ik_rag_engine"] = RAGEngine("ik_documents", api_key)
        else:
            return None
    return st.session_state.get("ik_rag_engine")


def _auto_load_documents():
    """
    IK prosedur dokumanini otomatik yukler ve RAG indexler.

    Agent acildiginda:
    1. yorglass_ik_prosedur.docx okunur
    2. Chunk'lara ayrilir
    3. RAG motoruna indexlenir
    """
    if st.session_state.get("ik_documents_indexed"):
        return

    doc_path = get_default_document_path()
    if not Path(doc_path).exists():
        return

    rag = _get_rag_engine()
    if not rag:
        return

    try:
        chunks = load_and_chunk_docx(doc_path)
        if chunks:
            rag.index_documents(chunks)
            st.session_state["ik_documents_indexed"] = True
            st.session_state["ik_chunk_count"] = len(chunks)
    except Exception as e:
        st.session_state["ik_index_error"] = str(e)


# ══════════════════════════════════════════════════════════════════════
# ANA RENDER FONKSIYONU
# ══════════════════════════════════════════════════════════════════════


def render_ik_agent():
    """IK Asistani agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "ik_chat_messages" not in st.session_state:
        st.session_state["ik_chat_messages"] = []
    if "ik_last_sources" not in st.session_state:
        st.session_state["ik_last_sources"] = []

    # ── Otomatik dokuman yukleme ve indexleme ──
    _auto_load_documents()

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("IK Dokuman Durumu")

        if st.session_state.get("ik_documents_indexed"):
            chunk_count = st.session_state.get("ik_chunk_count", 0)
            st.markdown(f'<span class="status-ok">Dokuman Yuklendi</span>', unsafe_allow_html=True)
            st.caption(f"RAG Index: {chunk_count} chunk indexlendi")
        elif st.session_state.get("ik_index_error"):
            st.markdown(f'<span class="status-err">Index Hatasi</span>', unsafe_allow_html=True)
            st.caption(st.session_state["ik_index_error"])
        else:
            st.markdown('<span class="status-err">Dokuman bulunamadi</span>', unsafe_allow_html=True)

        st.divider()

        # API durumu
        api_key = _get_api_key()
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:]
            st.markdown(f'<span class="status-ok">API Bagli</span> ({masked})', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-err">API anahtari bulunamadi</span>', unsafe_allow_html=True)

        st.divider()

        # Sohbeti temizle
        if st.button("Sohbeti Temizle", use_container_width=True, key="ik_clear_btn"):
            st.session_state["ik_chat_messages"] = []
            st.session_state["ik_last_sources"] = []
            st.rerun()

        # Ornek sorular
        st.subheader("Ornek Sorular")
        example_questions = [
            "Yillik izin hakkim kac gun?",
            "Fazla mesai ucreti nasil hesaplanir?",
            "Saglik raporu aldigimda ne yapmam gerekiyor?",
            "Evlilik izni kac gun?",
            "Is guvenligi kurallari nelerdir?",
            "Uzaktan calisma kosullari nedir?",
            "Kidem tazminati nasil hesaplanir?",
            "Performans degerlendirme kriterleri neler?",
        ]
        for q in example_questions:
            st.markdown(f"- _{q}_")

    # ══════════════════════════════════════════
    # ANA ICERIK - 2 KOLONLU LAYOUT
    # ══════════════════════════════════════════
    st.title("IK Asistani")
    st.markdown(
        "Yorglass IK prosedur ve politikalari hakkinda sorularinizi sorun. "
        "Cevaplar **sirket IK dokumani** kaynakli olup, sag panelde "
        "kaynak referanslari gosterilir."
    )

    # Dokuman yuklenmemisse uyari
    if not st.session_state.get("ik_documents_indexed"):
        st.warning(
            "IK dokumani yuklenemedi veya indexlenemedi. "
            "ik_agent/data/yorglass_ik_prosedur.docx dosyasini kontrol edin."
        )
        st.stop()

    # ── 2 kolonlu layout ──
    chat_col, source_col = st.columns([2, 1])

    # ── SAG PANEL: KAYNAK GOSTERIMI ──
    with source_col:
        st.subheader("Kaynak Referanslari")

        sources = st.session_state.get("ik_last_sources", [])
        if sources:
            for i, src in enumerate(sources):
                score_pct = int(src.get("score", 0) * 100)
                section = src.get("section_title", "Bilinmiyor")
                file_name = src.get("source_file", "")
                preview = src.get("text_preview", "")

                st.markdown(
                    f"**Kaynak {i+1}**\n\n"
                    f"**Dokuman:** {file_name}\n\n"
                    f"**Bolum:** {section}\n\n"
                    f"**Benzerlik:** %{score_pct}"
                )

                with st.expander("Metin Onizleme", expanded=False):
                    st.caption(preview + "..." if len(preview) >= 200 else preview)

                if i < len(sources) - 1:
                    st.divider()
        else:
            st.caption("Henuz bir soru sorulmadi. Soru sorduktan sonra cevabın kaynaklari burada gosterilecek.")

    # ── SOL PANEL: CHAT ──
    with chat_col:
        # Sabit yukseklikte scrollable chat alani
        chat_container = st.container(height=500)

        with chat_container:
            # Chat gecmisini goster
            for i, msg in enumerate(st.session_state["ik_chat_messages"]):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Bekleyen soru varsa → LLM cagir ve cevabi goster
            pending = st.session_state.get("ik_pending_question")
            if pending:
                with st.chat_message("assistant"):
                    with st.spinner("IK dokumanlari arastiriliyor..."):
                        rag = _get_rag_engine()
                        history = st.session_state["ik_chat_messages"][:-1]

                        response_text, sources = generate_ik_response(
                            pending, rag, history
                        )

                    st.markdown(response_text)

                # Yanitlari kaydet ve pending temizle
                st.session_state["ik_chat_messages"].append({
                    "role": "assistant",
                    "content": response_text,
                })
                st.session_state["ik_last_sources"] = sources
                st.session_state["ik_pending_question"] = None
                st.rerun()

        # Chat input - container disinda, altta sabit kalir
        if not api_key:
            st.warning("OpenAI API anahtari bulunamadi.")
            st.chat_input("Soru sorun...", disabled=True, key="ik_chat_disabled")
        else:
            if prompt := st.chat_input("IK ile ilgili sorunuzu sorun...", key="ik_chat_input"):
                # Kullanici mesajini hemen kaydet
                st.session_state["ik_chat_messages"].append({
                    "role": "user",
                    "content": prompt,
                })
                # Soruyu pending olarak isaretle ve rerun → soru hemen gorunur
                st.session_state["ik_pending_question"] = prompt
                st.rerun()
