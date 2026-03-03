"""
SQL Agent - Streamlit Sayfa Modulu.

SQL Generator agent'inin chat arayuzunu render eder.
Ana app.py'den cagirilir: render_sql_agent()
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from sql_agent.metadata_loader import (
    load_metadata_from_excel,
    get_table_summary,
    index_tables_for_rag,
)
from sql_agent.generator import generate_sql, extract_sql_block, _get_api_key
from sql_agent.visualizer import create_er_diagram_html, extract_fields_from_sql
from rag_engine import RAGEngine


def _get_rag_engine():
    """
    SQL Agent icin RAG motorunu dondurur.
    Session state'te yoksa olusturur.

    ── RAG: Her agent'in kendi ChromaDB koleksiyonu var ──
    SQL Agent → "sql_tables" koleksiyonu
    BAPI Agent → "bapi_functions" koleksiyonu
    """
    if "sql_rag_engine" not in st.session_state:
        api_key = _get_api_key()
        if api_key:
            st.session_state["sql_rag_engine"] = RAGEngine("sql_tables", api_key)
        else:
            return None
    return st.session_state.get("sql_rag_engine")


def render_sql_agent():
    """SQL Generator agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "sql_chat_messages" not in st.session_state:
        st.session_state["sql_chat_messages"] = []
    if "sql_tables" not in st.session_state:
        st.session_state["sql_tables"] = None
    if "sql_relationships" not in st.session_state:
        st.session_state["sql_relationships"] = None

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("SQL Metadata Yukleme")

        uploaded_file = st.file_uploader(
            "SAP Tablo Metadata Excel",
            type=["xlsx"],
            help="Tablolar ve Iliskiler sayfalarini iceren Excel dosyasi yukleyin",
            key="sql_excel_uploader",
        )

        if uploaded_file is not None:
            tables, relationships, error = load_metadata_from_excel(uploaded_file)
            if error:
                st.error(f"Excel okuma hatasi: {error}")
            else:
                st.session_state["sql_tables"] = tables
                st.session_state["sql_relationships"] = relationships

                # ══════════════════════════════════════════
                # RAG ADIM 1: INDEXLEME
                # Excel yuklendiginde tablolari RAG motoruna indexle
                # Her tablo icin embedding olusturulur ve
                # ChromaDB'ye kaydedilir
                # ══════════════════════════════════════════
                rag = _get_rag_engine()
                if rag:
                    index_tables_for_rag(tables, rag)
                    st.success(f"{len(tables)} tablo yuklendi ve indexlendi (RAG)")
                else:
                    st.success(f"{len(tables)} tablo yuklendi")

        # Ornek metadata yukleme butonu
        sample_path = Path(__file__).resolve().parent / "sample_metadata.xlsx"
        if sample_path.exists() and not st.session_state["sql_tables"]:
            if st.button("Ornek Metadata Yukle", use_container_width=True, type="primary", key="sql_sample_btn"):
                tables, relationships, error = load_metadata_from_excel(str(sample_path))
                if error:
                    st.error(f"Hata: {error}")
                else:
                    st.session_state["sql_tables"] = tables
                    st.session_state["sql_relationships"] = relationships
                    # RAG indexleme
                    rag = _get_rag_engine()
                    if rag:
                        index_tables_for_rag(tables, rag)
                    st.rerun()

        # Yuklenmis tablo ozeti
        if st.session_state["sql_tables"]:
            st.divider()
            st.subheader("Yuklenmis Tablolar")
            summary = get_table_summary(st.session_state["sql_tables"])
            st.markdown(summary, unsafe_allow_html=True)

            # RAG durumu
            rag = _get_rag_engine()
            if rag:
                count = rag.get_document_count()
                st.caption(f"RAG Index: {count} tablo indexlendi")

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
        if st.button("Sohbeti Temizle", use_container_width=True, key="sql_clear_btn"):
            st.session_state["sql_chat_messages"] = []
            st.rerun()

        # Ornek sorular
        st.subheader("Ornek Sorular")
        example_questions = [
            "Malzemenin bulundugu depolari getir",
            "Bu malzemenin rengi nedir?",
            "Serbest stoku sifirdan buyuk malzemeleri listele",
            "Malzeme tipi FERT olan malzemelerin tesis bilgilerini getir",
        ]
        for q in example_questions:
            st.markdown(f"- _{q}_")

    # ══════════════════════════════════════════
    # ANA ICERIK
    # ══════════════════════════════════════════
    st.title("SQL Generator Agent")
    st.markdown(
        "SAP tablo metadata'nizi yukleyin ve dogal dilde soru sorarak "
        "**SAP Open SQL (ABAP)** sorgusu uretin."
    )

    # Metadata yuklenmemisse uyari goster
    if not st.session_state["sql_tables"]:
        st.info(
            "Baslamak icin sol panelden SAP tablo metadata Excel dosyanizi yukleyin. "
            "Excel dosyasinda **Tablolar** ve **Iliskiler** adinda iki sayfa olmalidir."
        )
        st.stop()

    def _render_assistant_message(msg: dict, msg_index: int):
        """Asistan mesajini SQL blogu, aciklama ve diyagramla render eder."""
        st.markdown(msg["content"])

        used_tables = msg.get("used_tables", [])
        if used_tables:
            tables = st.session_state["sql_tables"]
            rels = st.session_state["sql_relationships"]
            sql_code = extract_sql_block(msg["content"])
            highlighted = extract_fields_from_sql(sql_code) if sql_code else None

            with st.expander("Tablo Iliski Diyagrami", expanded=True):
                html, height = create_er_diagram_html(tables, rels, used_tables, highlighted, sql_text=sql_code)
                display_h = min(height, 650)
                components.html(html, height=display_h, scrolling=True)

    # ── Chat gecmisini goster ──
    for i, msg in enumerate(st.session_state["sql_chat_messages"]):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _render_assistant_message(msg, i)
            else:
                st.markdown(msg["content"])

    # ── Chat input ──
    if not api_key:
        st.warning("OpenAI API anahtari bulunamadi. Lutfen `.env` dosyanizi kontrol edin.")
        st.chat_input("Soru sorun...", disabled=True, key="sql_chat_disabled")
    else:
        if prompt := st.chat_input("SAP tablosu hakkinda bir soru sorun...", key="sql_chat_input"):
            # Kullanici mesajini kaydet ve goster
            st.session_state["sql_chat_messages"].append({
                "role": "user",
                "content": prompt,
            })
            with st.chat_message("user"):
                st.markdown(prompt)

            # Asistan yaniti
            with st.chat_message("assistant"):
                with st.spinner("SQL sorgusu uretiliyor..."):
                    tables = st.session_state["sql_tables"]
                    rels = st.session_state["sql_relationships"]
                    history = st.session_state["sql_chat_messages"][:-1]

                    # ══════════════════════════════════════════
                    # RAG PIPELINE CALISIR:
                    # 1. rag_engine vector search yapar (RETRIEVAL)
                    # 2. Bulunan tablolar prompt'a eklenir (AUGMENTATION)
                    # 3. LLM SQL sorgusu uretir (GENERATION)
                    # ══════════════════════════════════════════
                    rag = _get_rag_engine()
                    response_text, used_tables = generate_sql(
                        prompt, tables, rels, history, rag_engine=rag
                    )

                    # Yapilandirilmis gosterim
                    st.markdown(response_text)

                    # ER diyagrami
                    if used_tables:
                        sql_code = extract_sql_block(response_text)
                        highlighted = extract_fields_from_sql(sql_code) if sql_code else None

                        with st.expander("Tablo Iliski Diyagrami", expanded=True):
                            html, height = create_er_diagram_html(tables, rels, used_tables, highlighted, sql_text=sql_code)
                            display_h = min(height, 650)
                            components.html(html, height=display_h, scrolling=True)

            # Asistan yanitini kaydet
            st.session_state["sql_chat_messages"].append({
                "role": "assistant",
                "content": response_text,
                "used_tables": used_tables,
            })
