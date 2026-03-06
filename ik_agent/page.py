"""
IK Agent - Streamlit Sayfa Modulu.

IK Asistani agent'inin arayuzunu render eder.
Iki tab icerir:
  Tab 1: IK Chatbot - Soru-cevap (RAG tabanli)
  Tab 2: CV Uygunluk Analizi - Toplu CV degerlendirme
"""
from pathlib import Path

import streamlit as st

from ik_agent.document_loader import load_and_chunk_docx, get_default_document_path
from ik_agent.generator import generate_ik_response, _get_api_key
from ik_agent.cv_analyzer import (
    analyze_multiple_cvs,
    format_criteria,
)
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
    # ANA ICERIK - TAB YAPISI
    # ══════════════════════════════════════════
    st.title("IK Asistani")

    tab_chatbot, tab_cv = st.tabs(["IK Chatbot", "CV Uygunluk Analizi"])

    with tab_chatbot:
        _render_chatbot_tab()

    with tab_cv:
        _render_cv_analyzer_tab()


# ══════════════════════════════════════════════════════════════════════
# TAB 1: IK CHATBOT
# ══════════════════════════════════════════════════════════════════════


def _render_chatbot_tab():
    """IK Chatbot tab icerigini render eder."""

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
        return

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
            st.caption("Henuz bir soru sorulmadi. Soru sorduktan sonra cevabin kaynaklari burada gosterilecek.")

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
        api_key = _get_api_key()
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


# ══════════════════════════════════════════════════════════════════════
# TAB 2: CV UYGUNLUK ANALIZI
# ══════════════════════════════════════════════════════════════════════


def _render_cv_analyzer_tab():
    """CV Uygunluk Analizi tab icerigini render eder."""

    st.markdown(
        "Pozisyon kriterlerini belirleyin ve aday CV'lerini (PDF) yukleyin. "
        "Sistem her CV'yi kriterlere gore puanlayip uygunluk sirasina gore listeler."
    )

    api_key = _get_api_key()
    if not api_key:
        st.warning("OpenAI API anahtari bulunamadi. CV analizi icin API anahtari gereklidir.")
        return

    # ── KRITER GIRISI ──
    st.subheader("Pozisyon Kriterleri")

    criteria_col1, criteria_col2 = st.columns(2)

    with criteria_col1:
        position = st.text_input(
            "Pozisyon Adi",
            placeholder="Ornek: Yazilim Gelistirici",
            key="cv_position",
        )
        experience_years = st.number_input(
            "Minimum Deneyim (Yil)",
            min_value=0,
            max_value=30,
            value=0,
            key="cv_experience",
        )
        education = st.selectbox(
            "Egitim Seviyesi",
            options=["", "Lise", "On Lisans", "Lisans", "Yuksek Lisans", "Doktora"],
            key="cv_education",
        )

    with criteria_col2:
        languages = st.text_input(
            "Dil Gereksinimleri",
            placeholder="Ornek: Ingilizce B2, Almanca A2",
            key="cv_languages",
        )
        skills = st.text_input(
            "Teknik Beceriler",
            placeholder="Ornek: Python, React, SAP, AutoCAD",
            key="cv_skills",
        )
        min_score = st.slider(
            "Minimum Uygunluk Esigi (%)",
            min_value=0,
            max_value=100,
            value=50,
            key="cv_min_score",
            help="Bu esik altindaki adaylar 'Uygun Degil' olarak isaretlenir.",
        )

    # Serbest metin (ek kriterler)
    extra_criteria = st.text_area(
        "Ek Kriterler (Opsiyonel)",
        placeholder="Ornek: Seyahat engeli olmamali, esnek calisma saatlerine uyum saglayabilmeli...",
        key="cv_extra_criteria",
        height=80,
    )

    st.divider()

    # ── CV YUKLEME ──
    st.subheader("CV Dosyalari")

    cv_files = st.file_uploader(
        "PDF formatinda CV dosyalarini yukleyin",
        type=["pdf"],
        accept_multiple_files=True,
        key="cv_files",
        help="Birden fazla PDF dosyasi secebilirsiniz.",
    )

    if cv_files:
        st.info(f"{len(cv_files)} adet CV yuklendi.")

    st.divider()

    # ── ANALIZ BUTONU ──
    col_btn, col_space = st.columns([1, 3])
    with col_btn:
        analyze_clicked = st.button(
            "Analiz Et",
            type="primary",
            use_container_width=True,
            key="cv_analyze_btn",
            disabled=not cv_files,
        )

    # ── ANALIZ ISLEMI ──
    if analyze_clicked and cv_files:
        # Kriter metnini olustur
        criteria_text = format_criteria(
            position=position,
            experience_years=experience_years,
            education=education,
            languages=languages,
            skills=skills,
            extra_criteria=extra_criteria,
        )

        if criteria_text == "Genel degerlendirme yapiniz.":
            st.warning("Lutfen en az bir kriter belirleyin.")
            return

        # Ilerleme cubugu
        progress_bar = st.progress(0, text="CV'ler analiz ediliyor...")
        status_text = st.empty()

        def update_progress(i, total, filename):
            progress = (i) / total
            progress_bar.progress(progress, text=f"Analiz ediliyor: {filename} ({i+1}/{total})")
            status_text.caption(f"Isleniyor: {filename}")

        # Toplu analiz
        results = analyze_multiple_cvs(
            cv_files=cv_files,
            criteria_text=criteria_text,
            api_key=api_key,
            progress_callback=update_progress,
        )

        progress_bar.progress(1.0, text="Analiz tamamlandi!")
        status_text.empty()

        # Sonuclari session state'e kaydet
        st.session_state["cv_results"] = results
        st.session_state["cv_min_score_used"] = min_score

    # ── SONUCLARI GOSTER ──
    results = st.session_state.get("cv_results")
    if results:
        _render_cv_results(results, st.session_state.get("cv_min_score_used", 50))


# ══════════════════════════════════════════════════════════════════════
# SONUC GOSTERIMI
# ══════════════════════════════════════════════════════════════════════


def _render_cv_results(results: list, min_score: int):
    """CV analiz sonuclarini gorsel olarak render eder."""

    st.subheader("Analiz Sonuclari")

    # Uygun ve uygun olmayan ayirimi
    uygun = [r for r in results if r.get("uygunluk_skoru", 0) >= min_score]
    uygun_degil = [r for r in results if r.get("uygunluk_skoru", 0) < min_score]

    # Ozet metrikler
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam CV", len(results))
    c2.metric("Uygun", len(uygun))
    c3.metric("Elenen", len(uygun_degil))
    if results:
        avg_score = sum(r.get("uygunluk_skoru", 0) for r in results) / len(results)
        c4.metric("Ortalama Skor", f"%{avg_score:.0f}")

    st.divider()

    # ── UYGUN ADAYLAR ──
    if uygun:
        st.markdown("### Uygun Adaylar")

        for i, result in enumerate(uygun):
            score = result.get("uygunluk_skoru", 0)
            name = result.get("aday_adi", "Bilinmiyor")
            filename = result.get("dosya_adi", "")
            summary = result.get("ozet", "")

            # Skor rengini belirle
            if score >= 80:
                score_color = "green"
            elif score >= 60:
                score_color = "orange"
            else:
                score_color = "red"

            # Aday karti
            with st.expander(
                f"**#{i+1}** | {name} | Skor: %{score} | {filename}",
                expanded=(i == 0),  # Ilk aday acik
            ):
                # Skor ve ozet
                st.markdown(f"**Uygunluk Skoru:** :{score_color}[%{score}]")
                st.markdown(f"**Ozet:** {summary}")

                # Guclu ve zayif yonler
                col_s, col_w = st.columns(2)

                with col_s:
                    st.markdown("**Guclu Yonler:**")
                    for item in result.get("guclu_yonler", []):
                        st.markdown(f"- {item}")

                with col_w:
                    st.markdown("**Zayif Yonler:**")
                    for item in result.get("zayif_yonler", []):
                        st.markdown(f"- {item}")

                # Kriter detay
                kriter_detay = result.get("kriter_detay", {})
                if kriter_detay:
                    st.markdown("**Kriter Bazli Puanlama:**")
                    for kriter_adi, detay in kriter_detay.items():
                        if isinstance(detay, dict):
                            k_skor = detay.get("skor", 0)
                            k_aciklama = detay.get("aciklama", "")
                            st.markdown(f"- **{kriter_adi.title()}:** %{k_skor} - {k_aciklama}")

    # ── ELENEN ADAYLAR ──
    if uygun_degil:
        st.divider()
        st.markdown("### Elenen Adaylar")
        st.caption(f"Minimum esik: %{min_score}")

        for result in uygun_degil:
            score = result.get("uygunluk_skoru", 0)
            name = result.get("aday_adi", "Bilinmiyor")
            filename = result.get("dosya_adi", "")
            summary = result.get("ozet", "")

            with st.expander(f"**{name}** | Skor: %{score} | {filename}"):
                st.markdown(f"**Ozet:** {summary}")

                zayif = result.get("zayif_yonler", [])
                if zayif:
                    st.markdown("**Elenme Nedenleri:**")
                    for item in zayif:
                        st.markdown(f"- {item}")
