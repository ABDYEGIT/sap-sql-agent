"""
SQL Agent - Streamlit Sayfa Modulu.

SQL Generator agent'inin chat arayuzunu render eder.
Multi-DB destegi: SAP (transactional) ve BW (Business Warehouse).
Intent Classifier ile otomatik DB secimi, Mermaid diagram ciktisi.
Ana app.py'den cagirilir: render_sql_agent()
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from config import SAP_METADATA_EXCEL, BW_METADATA_EXCEL
from sql_agent.metadata_loader import (
    load_metadata_from_excel,
    get_table_summary,
    index_tables_for_rag,
)
from sql_agent.generator import generate_sql, extract_sql_block, _get_api_key
from sql_agent.visualizer import create_er_diagram_html, extract_fields_from_sql
from sql_agent.intent_classifier import classify_intent
from sql_agent.diagram_generator import generate_flow_diagram, generate_er_diagram
from rag_engine import RAGEngine


def _get_rag_engine(db_type: str = "SAP"):
    """
    SQL Agent icin RAG motorunu dondurur.
    Session state'te yoksa olusturur.

    ── RAG: Her DB'nin kendi ChromaDB koleksiyonu var ──
    SAP → "sql_tables" koleksiyonu
    BW  → "bw_tables" koleksiyonu
    """
    key = "sql_rag_engine" if db_type == "SAP" else "bw_rag_engine"
    collection = "sql_tables" if db_type == "SAP" else "bw_tables"

    if key not in st.session_state:
        api_key = _get_api_key()
        if api_key:
            st.session_state[key] = RAGEngine(collection, api_key)
        else:
            return None
    return st.session_state.get(key)


def render_sql_agent():
    """SQL Generator agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "sql_chat_messages" not in st.session_state:
        st.session_state["sql_chat_messages"] = []
    if "sql_tables" not in st.session_state:
        st.session_state["sql_tables"] = None
    if "sql_relationships" not in st.session_state:
        st.session_state["sql_relationships"] = None
    if "bw_tables" not in st.session_state:
        st.session_state["bw_tables"] = None
    if "bw_relationships" not in st.session_state:
        st.session_state["bw_relationships"] = None

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        # ── DB Secimi ──
        st.subheader("Veritabani Secimi")
        db_mode = st.radio(
            "Hedef Veritabani",
            options=["Otomatik", "SAP", "BW"],
            index=0,
            key="sql_db_mode",
            help="Otomatik: Intent Classifier soruyu analiz ederek BW/SAP secimi yapar",
            horizontal=True,
        )

        st.divider()
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

                rag = _get_rag_engine("SAP")
                if rag:
                    try:
                        index_tables_for_rag(tables, rag)
                        st.success(f"{len(tables)} SAP tablo yuklendi ve indexlendi (RAG)")
                    except Exception as e:
                        st.warning(f"{len(tables)} tablo yuklendi (RAG indexleme hatasi: {e})")
                else:
                    st.success(f"{len(tables)} tablo yuklendi")

        # Ornek metadata yukleme butonu (SAP + BW)
        sample_path = Path(__file__).resolve().parent / "sample_metadata.xlsx"
        sap_data_path = Path(__file__).resolve().parent / "data" / "sap_metadata.xlsx"
        bw_data_path = Path(__file__).resolve().parent / "data" / "bw_metadata.xlsx"

        needs_sap = not st.session_state["sql_tables"]
        needs_bw = not st.session_state["bw_tables"]

        if (needs_sap or needs_bw):
            if st.button("Ornek Metadata Yukle (SAP + BW)", use_container_width=True, type="primary", key="sql_sample_btn"):
                # SAP metadata
                if needs_sap:
                    sap_src = sap_data_path if sap_data_path.exists() else sample_path
                    if sap_src.exists():
                        tables, rels, error = load_metadata_from_excel(str(sap_src))
                        if not error:
                            st.session_state["sql_tables"] = tables
                            st.session_state["sql_relationships"] = rels
                            rag = _get_rag_engine("SAP")
                            if rag:
                                try:
                                    index_tables_for_rag(tables, rag)
                                except Exception:
                                    pass

                # BW metadata
                if needs_bw and bw_data_path.exists():
                    bw_tbl, bw_rel, error = load_metadata_from_excel(str(bw_data_path))
                    if not error:
                        st.session_state["bw_tables"] = bw_tbl
                        st.session_state["bw_relationships"] = bw_rel
                        rag = _get_rag_engine("BW")
                        if rag:
                            try:
                                index_tables_for_rag(bw_tbl, rag)
                            except Exception:
                                pass

                st.rerun()

        # Yuklenmis tablo ozeti - SAP
        if st.session_state["sql_tables"]:
            st.divider()
            st.subheader("SAP Tablolari")
            summary = get_table_summary(st.session_state["sql_tables"])
            st.markdown(summary, unsafe_allow_html=True)
            rag = _get_rag_engine("SAP")
            if rag:
                count = rag.get_document_count()
                st.caption(f"SAP RAG Index: {count} tablo")

        # Yuklenmis tablo ozeti - BW
        if st.session_state["bw_tables"]:
            st.divider()
            st.subheader("BW Tablolari")
            summary = get_table_summary(st.session_state["bw_tables"])
            st.markdown(summary, unsafe_allow_html=True)
            rag = _get_rag_engine("BW")
            if rag:
                count = rag.get_document_count()
                st.caption(f"BW RAG Index: {count} tablo")

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
            "Serbest stoku sifirdan buyuk malzemeleri listele",
            "Aylik satis trendini goster (BW)",
            "Musteri bazli ciro analizi yap (BW)",
        ]
        for q in example_questions:
            st.markdown(f"- _{q}_")

    # ══════════════════════════════════════════
    # ANA ICERIK
    # ══════════════════════════════════════════
    st.title("SQL Generator Agent")
    st.markdown(
        "SAP / BW tablo metadata'nizi yukleyin ve dogal dilde soru sorarak "
        "**SAP Open SQL (ABAP)** sorgusu uretin. "
        "Otomatik modda Intent Classifier sorunuzu analiz eder."
    )

    # Metadata yuklenmemisse uyari goster
    has_any_metadata = st.session_state["sql_tables"] or st.session_state["bw_tables"]
    if not has_any_metadata:
        st.info(
            "Baslamak icin sol panelden SAP/BW tablo metadata Excel dosyanizi yukleyin "
            "veya **Ornek Metadata Yukle** butonuna basin."
        )
        st.stop()

    def _render_intent_badge(intent_info: dict):
        """Intent siniflandirma sonucunu badge olarak gosterir."""
        if not intent_info:
            return
        db = intent_info.get("db", "SAP")
        conf = intent_info.get("confidence", 0)
        reason = intent_info.get("reason", "")
        color = "#0891b2" if db == "BW" else "#16a34a"
        st.markdown(
            f'<div style="display:inline-flex;align-items:center;gap:8px;margin-bottom:8px;">'
            f'<span style="background:{color};color:#fff;padding:3px 10px;border-radius:12px;'
            f'font-size:13px;font-weight:600;">{db}</span>'
            f'<span style="color:#aaa;font-size:13px;">%{int(conf*100)} guven | {reason}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    def _render_mermaid(mermaid_code: str, key: str):
        """Mermaid diagramini Streamlit icerisinde render eder."""
        if not mermaid_code:
            return
        import base64
        graph_bytes = mermaid_code.encode("utf-8")
        encoded = base64.urlsafe_b64encode(graph_bytes).decode("ascii")
        img_url = f"https://mermaid.ink/svg/{encoded}?theme=dark&bgColor=!1e1e2e"
        st.image(img_url)

    def _render_assistant_message(msg: dict, msg_index: int):
        """Asistan mesajini SQL blogu, intent, diyagramlarla render eder."""
        # Intent badge
        intent_info = msg.get("intent")
        _render_intent_badge(intent_info)

        st.markdown(msg["content"])

        used_tables = msg.get("used_tables", [])
        target_db = msg.get("target_db", "SAP")

        # Mermaid akis diyagrami
        flow_mermaid = msg.get("flow_diagram")
        if flow_mermaid:
            with st.expander("Akis Diyagrami", expanded=False):
                _render_mermaid(flow_mermaid, f"flow_{msg_index}")

        # Mermaid ER diyagrami
        er_mermaid = msg.get("er_diagram")
        if er_mermaid:
            with st.expander("ER Diyagrami (Mermaid)", expanded=False):
                _render_mermaid(er_mermaid, f"er_{msg_index}")

        # Mevcut vis.js ER diyagrami
        if used_tables:
            tables = st.session_state["sql_tables"] if target_db == "SAP" else st.session_state["bw_tables"]
            rels = st.session_state["sql_relationships"] if target_db == "SAP" else st.session_state["bw_relationships"]
            if tables and rels is not None:
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
        if prompt := st.chat_input("SAP/BW tablosu hakkinda bir soru sorun...", key="sql_chat_input"):
            # Kullanici mesajini kaydet ve goster
            st.session_state["sql_chat_messages"].append({
                "role": "user",
                "content": prompt,
            })
            with st.chat_message("user"):
                st.markdown(prompt)

            # Asistan yaniti
            with st.chat_message("assistant"):
                # ── Intent Classification ──
                intent_info = None
                db_mode = st.session_state.get("sql_db_mode", "Otomatik")

                if db_mode == "Otomatik":
                    with st.spinner("Intent analiz ediliyor..."):
                        intent_info = classify_intent(prompt, api_key)
                        target_db = intent_info["db"]
                elif db_mode == "BW":
                    target_db = "BW"
                    intent_info = {"db": "BW", "confidence": 1.0, "reason": "Manuel secim"}
                else:
                    target_db = "SAP"
                    intent_info = {"db": "SAP", "confidence": 1.0, "reason": "Manuel secim"}

                _render_intent_badge(intent_info)

                # ── DB'ye gore metadata ve RAG sec ──
                if target_db == "BW" and st.session_state["bw_tables"]:
                    tables = st.session_state["bw_tables"]
                    rels = st.session_state["bw_relationships"]
                    rag = _get_rag_engine("BW")
                elif st.session_state["sql_tables"]:
                    tables = st.session_state["sql_tables"]
                    rels = st.session_state["sql_relationships"]
                    rag = _get_rag_engine("SAP")
                    target_db = "SAP"
                else:
                    st.error(f"{target_db} metadata yuklu degil. Lutfen metadata yukleyin.")
                    st.stop()

                with st.spinner(f"{target_db} SQL sorgusu uretiliyor..."):
                    history = st.session_state["sql_chat_messages"][:-1]

                    response_text, used_tables = generate_sql(
                        prompt, tables, rels, history,
                        rag_engine=rag, db_type=target_db,
                    )

                    # ── Mermaid Diagramlari ──
                    sql_code = extract_sql_block(response_text)
                    flow_diagram = generate_flow_diagram(prompt, intent_info, used_tables, sql_code)
                    er_diagram = generate_er_diagram(used_tables, tables, rels)

                    # Yapilandirilmis gosterim
                    st.markdown(response_text)

                    # Mermaid akis diyagrami
                    if flow_diagram:
                        with st.expander("Akis Diyagrami", expanded=False):
                            _render_mermaid(flow_diagram, "flow_live")

                    # Mermaid ER diyagrami
                    if er_diagram:
                        with st.expander("ER Diyagrami (Mermaid)", expanded=False):
                            _render_mermaid(er_diagram, "er_live")

                    # Mevcut vis.js ER diyagrami
                    if used_tables:
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
                "target_db": target_db,
                "intent": intent_info,
                "flow_diagram": flow_diagram,
                "er_diagram": er_diagram,
            })
