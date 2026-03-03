"""
BAPI Agent - Streamlit Sayfa Modulu.

BAPI Asistani agent'inin chat arayuzunu render eder.
Ana app.py'den cagirilir: render_bapi_agent()
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from bapi_agent.metadata_loader import (
    load_bapi_metadata_from_excel,
    get_bapi_summary,
    index_bapis_for_rag,
)
from bapi_agent.generator import generate_bapi_response, extract_used_bapis, _get_api_key
from bapi_agent.visualizer import create_bapi_parameter_html
from rag_engine import RAGEngine


def _get_rag_engine():
    """
    BAPI Agent icin RAG motorunu dondurur.

    ── RAG: BAPI Agent'in kendi ChromaDB koleksiyonu var ──
    SQL Agent → "sql_tables" koleksiyonu (ayri)
    BAPI Agent → "bapi_functions" koleksiyonu (ayri)
    """
    if "bapi_rag_engine" not in st.session_state:
        api_key = _get_api_key()
        if api_key:
            st.session_state["bapi_rag_engine"] = RAGEngine("bapi_functions", api_key)
        else:
            return None
    return st.session_state.get("bapi_rag_engine")


def render_bapi_agent():
    """BAPI Asistani agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "bapi_chat_messages" not in st.session_state:
        st.session_state["bapi_chat_messages"] = []
    if "bapi_metadata" not in st.session_state:
        st.session_state["bapi_metadata"] = None

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("BAPI Metadata Yukleme")

        uploaded_file = st.file_uploader(
            "SAP BAPI Metadata Excel",
            type=["xlsx"],
            help="BAPIler, Parametreler ve Parametre_Alanlari sayfalarini iceren Excel dosyasi",
            key="bapi_excel_uploader",
        )

        if uploaded_file is not None:
            bapis, error = load_bapi_metadata_from_excel(uploaded_file)
            if error:
                st.error(f"Excel okuma hatasi: {error}")
            else:
                st.session_state["bapi_metadata"] = bapis

                # ══════════════════════════════════════════
                # RAG ADIM 1: INDEXLEME
                # Excel yuklendiginde BAPI'leri RAG motoruna indexle
                # Her BAPI icin embedding olusturulur ve
                # ChromaDB'ye kaydedilir
                # ══════════════════════════════════════════
                rag = _get_rag_engine()
                if rag:
                    index_bapis_for_rag(bapis, rag)
                    st.success(f"{len(bapis)} BAPI yuklendi ve indexlendi (RAG)")
                else:
                    st.success(f"{len(bapis)} BAPI yuklendi")

        # Ornek metadata yukleme butonu
        sample_path = Path(__file__).resolve().parent / "bapi_sample_metadata.xlsx"
        if sample_path.exists() and not st.session_state["bapi_metadata"]:
            if st.button("Ornek BAPI Metadata Yukle", use_container_width=True, type="primary", key="bapi_sample_btn"):
                bapis, error = load_bapi_metadata_from_excel(str(sample_path))
                if error:
                    st.error(f"Hata: {error}")
                else:
                    st.session_state["bapi_metadata"] = bapis
                    # RAG indexleme
                    rag = _get_rag_engine()
                    if rag:
                        index_bapis_for_rag(bapis, rag)
                    st.rerun()

        # Yuklenmis BAPI ozeti
        if st.session_state["bapi_metadata"]:
            st.divider()
            st.subheader("Yuklenmis BAPI'ler")
            summary = get_bapi_summary(st.session_state["bapi_metadata"])
            st.markdown(summary, unsafe_allow_html=True)

            # RAG durumu
            rag = _get_rag_engine()
            if rag:
                count = rag.get_document_count()
                st.caption(f"RAG Index: {count} BAPI indexlendi")

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
        if st.button("Sohbeti Temizle", use_container_width=True, key="bapi_clear_btn"):
            st.session_state["bapi_chat_messages"] = []
            st.rerun()

        # Ornek sorular
        st.subheader("Ornek Sorular")
        example_questions = [
            "Malzeme genisletmek istiyorum",
            "Satin alma siparisi olusturmak istiyorum",
            "Tedarikci bilgilerini okumak istiyorum",
            "Malzeme stok bilgisini sorgulamak istiyorum",
        ]
        for q in example_questions:
            st.markdown(f"- _{q}_")

    # ══════════════════════════════════════════
    # ANA ICERIK
    # ══════════════════════════════════════════
    st.title("BAPI Asistani Agent")
    st.markdown(
        "SAP BAPI metadata'nizi yukleyin ve yapmak istediginiz islemi "
        "dogal dilde sorun. Size uygun **BAPI**'yi ve parametrelerini gosterecegim."
    )

    # Metadata yuklenmemisse uyari goster
    if not st.session_state["bapi_metadata"]:
        st.info(
            "Baslamak icin sol panelden SAP BAPI metadata Excel dosyanizi yukleyin. "
            "Excel'de **BAPIler**, **Parametreler** ve **Parametre_Alanlari** sayfalari olmalidir."
        )
        st.stop()

    def _render_assistant_message(msg: dict, msg_index: int):
        """Asistan mesajini BAPI aciklama ve parametre kartlariyla render eder."""
        st.markdown(msg["content"])

        used_bapis = msg.get("used_bapis", [])
        if used_bapis:
            bapis = st.session_state["bapi_metadata"]
            for bapi_name in used_bapis:
                if bapi_name in bapis:
                    with st.expander(f"Parametre Detaylari: {bapi_name}", expanded=True):
                        html, height = create_bapi_parameter_html(
                            bapi_name, bapis[bapi_name], used_bapis
                        )
                        if html:
                            components.html(html, height=height, scrolling=True)

    # ── Chat gecmisini goster ──
    for i, msg in enumerate(st.session_state["bapi_chat_messages"]):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _render_assistant_message(msg, i)
            else:
                st.markdown(msg["content"])

    # ── Chat input ──
    if not api_key:
        st.warning("OpenAI API anahtari bulunamadi. Lutfen `.env` dosyanizi kontrol edin.")
        st.chat_input("Soru sorun...", disabled=True, key="bapi_chat_disabled")
    else:
        if prompt := st.chat_input("Hangi islemi yapmak istiyorsunuz?", key="bapi_chat_input"):
            # Kullanici mesajini kaydet ve goster
            st.session_state["bapi_chat_messages"].append({
                "role": "user",
                "content": prompt,
            })
            with st.chat_message("user"):
                st.markdown(prompt)

            # Asistan yaniti
            with st.chat_message("assistant"):
                with st.spinner("BAPI arastiriliyor..."):
                    bapis = st.session_state["bapi_metadata"]
                    history = st.session_state["bapi_chat_messages"][:-1]

                    # ══════════════════════════════════════════
                    # RAG PIPELINE CALISIR:
                    # 1. rag_engine vector search yapar (RETRIEVAL)
                    # 2. Bulunan BAPI'ler prompt'a eklenir (AUGMENTATION)
                    # 3. LLM BAPI onerisi uretir (GENERATION)
                    # ══════════════════════════════════════════
                    rag = _get_rag_engine()
                    response_text, used_bapis = generate_bapi_response(
                        prompt, bapis, history, rag_engine=rag
                    )

                    st.markdown(response_text)

                    # BAPI parametre kartlari
                    if used_bapis:
                        for bapi_name in used_bapis:
                            if bapi_name in bapis:
                                with st.expander(f"Parametre Detaylari: {bapi_name}", expanded=True):
                                    html, height = create_bapi_parameter_html(
                                        bapi_name, bapis[bapi_name], used_bapis
                                    )
                                    if html:
                                        components.html(html, height=height, scrolling=True)

            # Asistan yanitini kaydet
            st.session_state["bapi_chat_messages"].append({
                "role": "assistant",
                "content": response_text,
                "used_bapis": used_bapis,
            })
