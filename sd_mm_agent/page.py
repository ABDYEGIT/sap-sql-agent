"""
SD/MM Agent - Orkestrator Sayfa Modulu.

SD (Sales & Distribution) ve MM (Materials Management) modulleri icin
birlesik agent arayuzunu render eder.

ORKESTRASYON AKISI:
1. Kullanici soru sorar
2. Intent Detection → SQL mi BAPI mi?
3. SQL yolu: generate_sql() → SAP SQL → SQLite SQL → Calistir → DataFrame goster
4. BAPI yolu: generate_bapi_response() → BAPI aciklama + parametre kartlari

Bu agent, sql_agent ve bapi_agent modullerini "tool" olarak kullanir.
Manuel Excel yukleme gerekmez - mock veriler otomatik yuklenir.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ── SD/MM Agent kendi modulleri ──
from sd_mm_agent.mock_db import get_db_connection, get_table_counts
from sd_mm_agent.intent_detector import detect_intent
from sd_mm_agent.sql_executor import convert_sap_to_sqlite, execute_query

# ── SQL Agent "tool" olarak kullaniliyor ──
from sql_agent.generator import generate_sql, extract_sql_block, extract_used_tables, _get_api_key
from sql_agent.metadata_loader import (
    load_metadata_from_excel,
    index_tables_for_rag,
)

# ── BAPI Agent "tool" olarak kullaniliyor ──
from bapi_agent.generator import generate_bapi_response, extract_used_bapis
from bapi_agent.metadata_loader import (
    load_bapi_metadata_from_excel,
    index_bapis_for_rag,
)
from bapi_agent.visualizer import create_bapi_parameter_html

# ── Ortak RAG Motoru ──
from rag_engine import RAGEngine


# ══════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSIYONLAR
# ══════════════════════════════════════════════════════════════════════


def _get_sql_rag_engine():
    """
    SD/MM Agent icin SQL RAG motorunu dondurur.

    ── RAG: SD/MM Agent'in kendi ChromaDB koleksiyonu var ──
    SQL Agent → "sql_tables" (ayri)
    SD/MM Agent → "sdmm_sql_tables" (ayri)
    """
    if "sdmm_sql_rag" not in st.session_state:
        api_key = _get_api_key()
        if api_key:
            st.session_state["sdmm_sql_rag"] = RAGEngine("sdmm_sql_tables", api_key)
        else:
            return None
    return st.session_state.get("sdmm_sql_rag")


def _get_bapi_rag_engine():
    """
    SD/MM Agent icin BAPI RAG motorunu dondurur.

    ── RAG: SD/MM Agent'in kendi BAPI ChromaDB koleksiyonu var ──
    BAPI Agent → "bapi_functions" (ayri)
    SD/MM Agent → "sdmm_bapi_functions" (ayri)
    """
    if "sdmm_bapi_rag" not in st.session_state:
        api_key = _get_api_key()
        if api_key:
            st.session_state["sdmm_bapi_rag"] = RAGEngine("sdmm_bapi_functions", api_key)
        else:
            return None
    return st.session_state.get("sdmm_bapi_rag")


def _auto_load_metadata():
    """
    Ornek metadata Excel'lerini otomatik yukler ve RAG indexler.

    ── OTOMATIK BASLATMA: Manuel Excel yukleme gerekmez ──
    SD/MM Agent acildiginda:
    1. sql_agent/sample_metadata.xlsx → SQL tablolari + RAG index
    2. bapi_agent/bapi_sample_metadata.xlsx → BAPI'ler + RAG index
    3. mock_db → SQLite veritabani olusturulur
    """
    # ── SQL Metadata Yukleme ──
    if "sdmm_sql_tables" not in st.session_state:
        sql_excel = Path(__file__).resolve().parent.parent / "sql_agent" / "sample_metadata.xlsx"
        if sql_excel.exists():
            tables, relationships, error = load_metadata_from_excel(str(sql_excel))
            if not error:
                st.session_state["sdmm_sql_tables"] = tables
                st.session_state["sdmm_sql_relationships"] = relationships

                # RAG Indexleme
                rag = _get_sql_rag_engine()
                if rag:
                    try:
                        index_tables_for_rag(tables, rag)
                    except Exception:
                        pass

    # ── BAPI Metadata Yukleme ──
    if "sdmm_bapi_metadata" not in st.session_state:
        bapi_excel = Path(__file__).resolve().parent.parent / "bapi_agent" / "bapi_sample_metadata.xlsx"
        if bapi_excel.exists():
            bapis, error = load_bapi_metadata_from_excel(str(bapi_excel))
            if not error:
                st.session_state["sdmm_bapi_metadata"] = bapis

                # RAG Indexleme
                rag = _get_bapi_rag_engine()
                if rag:
                    try:
                        index_bapis_for_rag(bapis, rag)
                    except Exception:
                        pass

    # ── Mock DB Baglantisi ──
    get_db_connection()


# ══════════════════════════════════════════════════════════════════════
# ANA RENDER FONKSIYONU
# ══════════════════════════════════════════════════════════════════════


def render_sdmm_agent():
    """SD/MM Combined Agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "sdmm_chat_messages" not in st.session_state:
        st.session_state["sdmm_chat_messages"] = []

    # ── Otomatik metadata ve mock DB yukleme ──
    _auto_load_metadata()

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("Mock Veritabani")

        # Mock DB tablo sayilari
        db_conn = get_db_connection()
        counts = get_table_counts(db_conn)
        total_records = sum(counts.values())

        st.markdown(f"**Toplam:** {total_records} kayit, {len(counts)} tablo")

        with st.expander("Tablo Detaylari", expanded=False):
            for table_name, count in sorted(counts.items()):
                st.markdown(f"- **{table_name}**: {count} kayit")

        # RAG durumu
        sql_rag = _get_sql_rag_engine()
        bapi_rag = _get_bapi_rag_engine()

        st.divider()
        st.subheader("RAG Durumu")

        if sql_rag:
            sql_count = sql_rag.get_document_count()
            st.caption(f"SQL Index: {sql_count} tablo indexlendi")
        if bapi_rag:
            bapi_count = bapi_rag.get_document_count()
            st.caption(f"BAPI Index: {bapi_count} BAPI indexlendi")

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
        if st.button("Sohbeti Temizle", use_container_width=True, key="sdmm_clear_btn"):
            st.session_state["sdmm_chat_messages"] = []
            st.rerun()

        # Ornek sorular
        st.subheader("Ornek Sorular")
        example_questions = [
            "Tum malzemeleri listele",
            "Stoku 100'den fazla olan malzemeler",
            "Bronz cam cesitlerini goster",
            "En pahali 5 siparis kalemini getir",
            "Hangi tedarikci hangi malzemeyi sagliyor?",
            "Malzeme olusturmak istiyorum",
            "Satin alma siparisi acmak istiyorum",
        ]
        for q in example_questions:
            st.markdown(f"- _{q}_")

    # ══════════════════════════════════════════
    # ANA ICERIK
    # ══════════════════════════════════════════
    st.title("SD/MM Agent")
    st.markdown(
        "SAP **SD** (Satis & Dagitim) ve **MM** (Malzeme Yonetimi) modulleri icin "
        "birlesik agent. Sorunuzu yazmaya baslayin - intent detection ile "
        "**SQL sorgulama** veya **BAPI islem** rehberi otomatik secilir."
    )

    # Metadata kontrol
    if not st.session_state.get("sdmm_sql_tables"):
        st.error("SQL metadata yuklenemedi. sql_agent/sample_metadata.xlsx dosyasini kontrol edin.")
        st.stop()

    # ── Chat gecmisini goster ──
    for i, msg in enumerate(st.session_state["sdmm_chat_messages"]):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _render_assistant_message(msg, i)
            else:
                st.markdown(msg["content"])

    # ── Chat input ──
    if not api_key:
        st.warning("OpenAI API anahtari bulunamadi. Lutfen `.env` dosyanizi kontrol edin.")
        st.chat_input("Soru sorun...", disabled=True, key="sdmm_chat_disabled")
    else:
        if prompt := st.chat_input("SD/MM ile ilgili sorunuzu sorun...", key="sdmm_chat_input"):
            # Kullanici mesajini kaydet ve goster
            st.session_state["sdmm_chat_messages"].append({
                "role": "user",
                "content": prompt,
            })
            with st.chat_message("user"):
                st.markdown(prompt)

            # ══════════════════════════════════════════
            # ORKESTRASYON: Intent Detection + Routing
            # ══════════════════════════════════════════
            with st.chat_message("assistant"):
                # ── ADIM 1: Intent Detection ──
                with st.spinner("Niyet analiz ediliyor..."):
                    intent = detect_intent(prompt)

                if intent == "SQL":
                    _handle_sql_intent(prompt)
                else:
                    _handle_bapi_intent(prompt)


# ══════════════════════════════════════════════════════════════════════
# SQL INTENT HANDLER
# ══════════════════════════════════════════════════════════════════════
# Intent "SQL" ise:
# 1. sql_agent.generate_sql() ile SAP Open SQL uret
# 2. extract_sql_block() ile SQL'i cikar
# 3. convert_sap_to_sqlite() ile SQLite SQL'e cevir
# 4. execute_query() ile mock DB'de calistir
# 5. Hem SAP SQL hem DataFrame sonucunu goster
# ══════════════════════════════════════════════════════════════════════


def _handle_sql_intent(prompt: str):
    """SQL intent'i icin: SAP SQL uret → SQLite'a cevir → Calistir → Sonuc goster."""

    st.info("Intent: **SQL Sorgulama** | SQL Agent calisiyor...")

    tables = st.session_state["sdmm_sql_tables"]
    relationships = st.session_state.get("sdmm_sql_relationships", [])
    history = st.session_state["sdmm_chat_messages"][:-1]
    rag = _get_sql_rag_engine()

    # ── ADIM 2: SAP Open SQL Uret (sql_agent tool olarak kullaniliyor) ──
    with st.spinner("SAP Open SQL sorgusu uretiliyor..."):
        response_text, used_tables = generate_sql(
            prompt, tables, relationships, history, rag_engine=rag
        )

    # LLM yanitini goster
    st.markdown(response_text)

    # ── ADIM 3: SQL Blogunu Cikar ──
    sap_sql = extract_sql_block(response_text)

    df_result = None
    sqlite_sql = None
    sql_error = None

    if sap_sql:
        # ── ADIM 4: SAP SQL → SQLite SQL ──
        sqlite_sql = convert_sap_to_sqlite(sap_sql)

        if sqlite_sql:
            # ── ADIM 5: Mock DB'de Calistir ──
            db_conn = get_db_connection()
            df_result, sql_error = execute_query(sqlite_sql, db_conn)

        # Sonuclari goster
        st.divider()
        st.subheader("Sorgu Sonuclari")

        # SQLite cevirisi bilgisi
        with st.expander("SQL Cevirisi Detayi", expanded=False):
            st.markdown("**SAP Open SQL:**")
            st.code(sap_sql, language="sql")
            if sqlite_sql:
                st.markdown("**SQLite SQL:**")
                st.code(sqlite_sql, language="sql")

        if sql_error:
            st.error(f"Sorgu hatasi: {sql_error}")
        elif df_result is not None and not df_result.empty:
            st.success(f"{len(df_result)} kayit bulundu")
            st.dataframe(df_result, use_container_width=True)
        elif df_result is not None and df_result.empty:
            st.warning("Sorgu basarili ancak sonuc bulunamadi (0 kayit)")
        else:
            st.warning("SQL blogu islendi ancak sonuc alinamadi")

    # Asistan yanitini kaydet
    st.session_state["sdmm_chat_messages"].append({
        "role": "assistant",
        "content": response_text,
        "intent": "SQL",
        "used_tables": used_tables,
        "sap_sql": sap_sql,
        "sqlite_sql": sqlite_sql,
        "df_result": df_result if df_result is not None else None,
        "sql_error": sql_error,
    })


# ══════════════════════════════════════════════════════════════════════
# BAPI INTENT HANDLER
# ══════════════════════════════════════════════════════════════════════
# Intent "BAPI" ise:
# 1. bapi_agent.generate_bapi_response() ile BAPI onerisi uret
# 2. create_bapi_parameter_html() ile parametre kartlarini goster
# ══════════════════════════════════════════════════════════════════════


def _handle_bapi_intent(prompt: str):
    """BAPI intent'i icin: BAPI onerisi uret → Parametre kartlarini goster."""

    st.info("Intent: **BAPI Islemi** | BAPI Agent calisiyor...")

    bapis = st.session_state.get("sdmm_bapi_metadata", {})
    history = st.session_state["sdmm_chat_messages"][:-1]
    rag = _get_bapi_rag_engine()

    if not bapis:
        st.warning("BAPI metadata yuklenmemis. bapi_agent/bapi_sample_metadata.xlsx kontrol edin.")
        st.session_state["sdmm_chat_messages"].append({
            "role": "assistant",
            "content": "BAPI metadata bulunamadi.",
            "intent": "BAPI",
            "used_bapis": [],
        })
        return

    # ── BAPI Agent tool olarak kullaniliyor ──
    with st.spinner("BAPI arastiriliyor..."):
        response_text, used_bapis = generate_bapi_response(
            prompt, bapis, history, rag_engine=rag
        )

    st.markdown(response_text)

    # Asistan yanitini kaydet
    st.session_state["sdmm_chat_messages"].append({
        "role": "assistant",
        "content": response_text,
        "intent": "BAPI",
        "used_bapis": used_bapis,
    })


# ══════════════════════════════════════════════════════════════════════
# ASISTAN MESAJI RENDER
# ══════════════════════════════════════════════════════════════════════


def _render_assistant_message(msg: dict, msg_index: int):
    """Asistan mesajini intent'e gore render eder (chat gecmisinde tekrar gosterme)."""
    intent = msg.get("intent", "SQL")

    # Intent badge'i goster
    if intent == "SQL":
        st.info("Intent: **SQL Sorgulama**")
    else:
        st.info("Intent: **BAPI Islemi**")

    # Ana yaniit metni
    st.markdown(msg["content"])

    # SQL sonuclari (varsa)
    if intent == "SQL":
        sap_sql = msg.get("sap_sql")
        sqlite_sql = msg.get("sqlite_sql")
        df_result = msg.get("df_result")
        sql_error = msg.get("sql_error")

        if sap_sql:
            st.divider()
            st.subheader("Sorgu Sonuclari")

            with st.expander("SQL Cevirisi Detayi", expanded=False):
                st.markdown("**SAP Open SQL:**")
                st.code(sap_sql, language="sql")
                if sqlite_sql:
                    st.markdown("**SQLite SQL:**")
                    st.code(sqlite_sql, language="sql")

            if sql_error:
                st.error(f"Sorgu hatasi: {sql_error}")
            elif df_result is not None and not df_result.empty:
                st.success(f"{len(df_result)} kayit bulundu")
                st.dataframe(df_result, use_container_width=True)
            elif df_result is not None and df_result.empty:
                st.warning("Sonuc bulunamadi (0 kayit)")

    # BAPI kartlari (varsa)
    elif intent == "BAPI":
        used_bapis = msg.get("used_bapis", [])
        bapis = st.session_state.get("sdmm_bapi_metadata", {})

        if used_bapis:
            for bapi_name in used_bapis:
                if bapi_name in bapis:
                    with st.expander(f"Parametre Detaylari: {bapi_name}", expanded=True):
                        html, height = create_bapi_parameter_html(
                            bapi_name, bapis[bapi_name], used_bapis
                        )
                        if html:
                            components.html(html, height=height, scrolling=True)
